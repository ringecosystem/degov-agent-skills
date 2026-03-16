#!/usr/bin/env node

import { ExactEvmScheme, toClientEvmSigner } from '@x402/evm';
import { wrapFetchWithPaymentFromConfig } from '@x402/fetch';
import { createPublicClient, http } from 'viem';
import { base } from 'viem/chains';
import {
  DEFAULT_WALLET_PATH,
  getAccount,
  getResolvedWalletPath,
  getUsdcBalance,
  initWallet,
} from './wallet-store.js';

const API_BASE_URL = process.env.DEGOV_AGENT_API_BASE_URL || 'http://127.0.0.1:3310';

const FALLBACK_PRICES = {
  daos: 0.005,
  activity: 0.005,
  freshness: 0.005,
  brief: 0.02,
  item: 0.02,
} as const;

const ITEM_KINDS = new Set(['proposal', 'forum_topic']);
const YELLOW = process.stdout.isTTY ? '\x1b[33m' : '';
const RESET = process.stdout.isTTY ? '\x1b[0m' : '';

interface PricingResponse {
  request: { endpoint: string };
  pricing: {
    token: string;
    network: string;
    entries: Record<keyof typeof FALLBACK_PRICES, { price: string }>;
  };
}

interface PricingInfo {
  prices: Record<keyof typeof FALLBACK_PRICES, number>;
  source: 'live' | 'fallback';
  token: string;
  network: string;
}

interface ParsedArgs {
  _: string[];
  [key: string]: string | boolean | string[];
}

function parseArgs(argv: string[]): ParsedArgs {
  const args: ParsedArgs = { _: [] };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith('--')) {
      args._.push(arg);
      continue;
    }

    const next = argv[index + 1];
    if (next && !next.startsWith('--')) {
      args[arg] = next;
      index += 1;
      continue;
    }

    args[arg] = true;
  }

  return args;
}

function getArgValue(args: ParsedArgs, name: string): string | undefined {
  const value = args[name];
  return typeof value === 'string' ? value : undefined;
}

async function getPaymentClient(): Promise<{
  accountAddress: `0x${string}`;
  fetchWithPayment: typeof fetch;
}> {
  const { account } = await getAccount();
  const publicClient = createPublicClient({
    chain: base,
    transport: http('https://mainnet.base.org'),
  });
  const signer = toClientEvmSigner(account, publicClient);

  return {
    accountAddress: account.address,
    fetchWithPayment: wrapFetchWithPaymentFromConfig(fetch, {
      schemes: [
        {
          network: 'eip155:8453',
          client: new ExactEvmScheme(signer),
        },
      ],
    }),
  };
}

async function apiCall(endpoint: string): Promise<unknown> {
  const { accountAddress, fetchWithPayment } = await getPaymentClient();
  const url = `${API_BASE_URL}${endpoint}`;

  console.error(`Using wallet: ${accountAddress}`);
  console.error(`Calling: ${url}`);

  const response = await fetchWithPayment(url);
  const text = await response.text();

  let payload: unknown = text;
  try {
    payload = JSON.parse(text) as unknown;
  } catch {
    payload = text;
  }

  if (!response.ok) {
    const detail = typeof payload === 'string' ? payload : JSON.stringify(payload);
    throw new Error(`API error ${response.status}: ${detail}`);
  }

  return payload;
}

function printJson(value: unknown): void {
  console.log(JSON.stringify(value, null, 2));
}

function getBudgetRecommendation(requests: Record<keyof typeof FALLBACK_PRICES, number>): string[] {
  const lowCostCapacity = Math.min(requests.daos, requests.activity, requests.freshness);
  const detailCapacity = Math.min(requests.brief, requests.item);

  if (lowCostCapacity < 20 || detailCapacity < 5) {
    return [
      'Recommendation: this is a very small budget. Use it for a few quick checks only.',
      'Good fit: test one DAO, open a few recent activity items, then stop and review the results.',
    ];
  }

  if (lowCostCapacity < 100 || detailCapacity < 20) {
    return [
      'Recommendation: this is a light testing budget.',
      'Good fit: explore one or two DAOs and inspect a small number of detail pages.',
    ];
  }

  if (lowCostCapacity < 300 || detailCapacity < 60) {
    return [
      'Recommendation: this is a solid everyday research budget.',
      'Good fit: compare several DAOs, review recent activity, and open a moderate number of detail pages.',
    ];
  }

  return [
    'Recommendation: this is a large research budget.',
    'Good fit: multi-DAO scans, repeated follow-up checks, and deeper proposal or forum review over time.',
  ];
}

async function getPricing(): Promise<PricingInfo> {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/meta/pricing`);
    if (!response.ok) {
      throw new Error(`pricing metadata returned ${response.status}`);
    }

    const payload = (await response.json()) as PricingResponse;
    return {
      prices: {
        daos: Number(payload.pricing.entries.daos.price),
        activity: Number(payload.pricing.entries.activity.price),
        freshness: Number(payload.pricing.entries.freshness.price),
        brief: Number(payload.pricing.entries.brief.price),
        item: Number(payload.pricing.entries.item.price),
      },
      source: 'live',
      token: payload.pricing.token,
      network: payload.pricing.network,
    };
  } catch {
    return {
      prices: { ...FALLBACK_PRICES },
      source: 'fallback',
      token: 'usdc',
      network: 'base',
    };
  }
}

function formatUsdAmount(value: number): string {
  if (value >= 1) {
    return value.toFixed(2).replace(/\.00$/, '');
  }
  if (value >= 0.1) {
    return value.toFixed(3).replace(/0+$/, '').replace(/\.$/, '');
  }
  return value.toFixed(4).replace(/0+$/, '').replace(/\.$/, '');
}

function getFundingRecommendations(pricing: PricingInfo): string[] {
  const priceValues = Object.values(pricing.prices);
  const minPrice = Math.min(...priceValues);
  const maxPrice = Math.max(...priceValues);

  const bands = [
    { label: 'light usage (1-10 calls/day)', minCalls: 1, maxCalls: 10 },
    { label: 'moderate usage (10-100 calls/day)', minCalls: 10, maxCalls: 100 },
    { label: 'heavy usage (100+ calls/day)', minCalls: 100, maxCalls: 250 },
  ];

  return bands.map((band) => {
    const monthlyMin = band.minCalls * minPrice * 30;
    const monthlyMax = band.maxCalls * maxPrice * 30;
    const range =
      band.label === 'heavy usage (100+ calls/day)'
        ? `${formatUsdAmount(monthlyMin)}+ ${pricing.token}`
        : `${formatUsdAmount(monthlyMin)}-${formatUsdAmount(monthlyMax)} ${pricing.token}`;

    return `- For ${band.label}, a rough 30-day budget is ${range}.`;
  });
}

async function printBudget(amountUsd: string): Promise<void> {
  const amount = Number(amountUsd);
  if (!Number.isFinite(amount) || amount <= 0) {
    throw new Error('Budget amount must be a positive number.');
  }

  const pricing = await getPricing();
  const requests = Object.fromEntries(
    Object.entries(pricing.prices).map(([key, price]) => [key, Math.floor(amount / price)])
  ) as Record<keyof typeof FALLBACK_PRICES, number>;

  printJson({
    network: pricing.network,
    requests,
    source: pricing.source,
    token: pricing.token,
    usd: amount,
  });

  console.log('');
  for (const line of getBudgetRecommendation(requests)) {
    console.log(line);
  }
}

const commands: Record<string, (args: ParsedArgs) => Promise<void>> = {
  async wallet(args) {
    const subcommand = args._[0] || 'help';

    if (subcommand === 'init') {
      const result = await initWallet();
      const pricing = await getPricing();
      console.log(result.created ? 'Created payment wallet.' : 'Wallet already exists.');
      printJson({
        address: result.address,
        encrypted: result.encrypted,
        walletPath: result.walletPath,
      });
      console.log('');
      console.log(
        `${YELLOW}This wallet is used only to pay small x402 fees when the skill calls degov-agent-api.${RESET}`
      );
      console.log(
        `${YELLOW}It helps keep API payments separate from your main wallet, fund this Base address with a small amount of USDC for paid API calls.${RESET}`
      );
      console.log('');
      console.log('The recommended amount depends on your expected usage:');
      console.log('');
      for (const line of getFundingRecommendations(pricing)) {
        console.log(line);
      }
      console.log('');
      console.log(`${YELLOW}Do not transfer large amounts of money to this wallet.${RESET}`);
      console.log(`${YELLOW}A small testing balance is the safer default.${RESET}`);
      return;
    }

    if (subcommand === 'address') {
      const { account, walletPath, wallet } = await getAccount();
      printJson({
        address: account.address,
        encrypted: Boolean(wallet.crypto),
        walletPath,
      });
      return;
    }

    if (subcommand === 'balance') {
      const { account, walletPath, wallet } = await getAccount();
      const balance = await getUsdcBalance(account.address);
      printJson({
        address: account.address,
        asset: 'USDC',
        balance: balance.formatted,
        encrypted: Boolean(wallet.crypto),
        network: 'Base Mainnet',
        raw: balance.raw.toString(),
        walletPath,
      });
      return;
    }

    throw new Error('Usage: pnpm exec tsx degov-client.ts wallet <init|address|balance>');
  },

  async budget(args) {
    await printBudget(getArgValue(args, '--usd') || '1');
  },

  async daos() {
    const data = await apiCall('/v1/daos');
    printJson(data);
  },

  async activity(args) {
    const params = new URLSearchParams();
    const daoId = getArgValue(args, '--dao');
    const hours = getArgValue(args, '--hours');
    const limit = getArgValue(args, '--limit');
    const types = getArgValue(args, '--types');

    if (daoId) params.set('dao_id', daoId);
    if (hours) params.set('hours', hours);
    if (limit) params.set('limit', limit);
    if (types) params.set('types', types);
    if (args['--governance'] === true) params.set('governance_only', 'true');

    const query = params.toString();
    const data = await apiCall(`/v1/activity${query ? `?${query}` : ''}`);
    printJson(data);
  },

  async brief(args) {
    const daoId = args._[0];
    if (!daoId) {
      throw new Error('Usage: pnpm exec tsx degov-client.ts brief <dao-id> [--activity-limit N]');
    }

    const params = new URLSearchParams();
    const activityLimit = getArgValue(args, '--activity-limit');
    if (activityLimit) params.set('activity_limit', activityLimit);

    const query = params.toString();
    const data = await apiCall(`/v1/daos/${daoId}/brief${query ? `?${query}` : ''}`);
    printJson(data);
  },

  async item(args) {
    const kind = args._[0];
    const externalId = args._[1];

    if (!kind || !externalId) {
      throw new Error(
        'Usage: pnpm exec tsx degov-client.ts item <proposal|forum_topic> <external-id>'
      );
    }

    if (!ITEM_KINDS.has(kind)) {
      throw new Error('Unsupported item kind. Use one of: proposal, forum_topic');
    }

    const data = await apiCall(`/v1/items/${kind}/${externalId}`);
    printJson(data);
  },

  async freshness() {
    const data = await apiCall('/v1/system/freshness');
    printJson(data);
  },

  async health() {
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = (await response.json()) as unknown;

    if (!response.ok) {
      throw new Error(`API error ${response.status}: ${JSON.stringify(data)}`);
    }

    printJson(data);
  },

  async help() {
    console.log(`DAO Governance Client

Wallet storage:
  default ${DEFAULT_WALLET_PATH}
  resolved ${getResolvedWalletPath()}

Environment:
  DEGOV_AGENT_API_BASE_URL      default ${API_BASE_URL}
  DEGOV_AGENT_WALLET_PATH       optional wallet file override
  DEGOV_AGENT_WALLET_PASSPHRASE required for non-interactive encrypted wallet use

Commands:
  wallet init                   create or reuse local payment wallet
  wallet address                show wallet address and path
  wallet balance                show Base USDC balance
  budget --usd 1                estimate requests using live API pricing
  daos                          list DAOs
  activity [--dao ens] [--hours 24] [--limit 10] [--types proposal,forum_topic] [--governance]
  brief <dao-id> [--activity-limit 6]
  item <proposal|forum_topic> <external-id>
  freshness
  health
  help
`);
  },
};

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const command = args._[0] || 'help';
  args._.shift();

  const handler = commands[command];
  if (!handler) {
    throw new Error(`Unknown command: ${command}`);
  }

  await handler(args);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exit(1);
});
