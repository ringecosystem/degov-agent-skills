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
<<<<<<< HEAD
  migrateWallet,
=======
>>>>>>> f76e1bf (refactor: move dao governance client to typescript)
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

interface PricingResponse {
  request: { endpoint: string };
  pricing: {
    token: string;
    network: string;
    entries: Record<keyof typeof FALLBACK_PRICES, { price: string }>;
  };
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

async function getPricing(): Promise<{
  prices: Record<keyof typeof FALLBACK_PRICES, number>;
  source: 'live' | 'fallback';
  token: string;
  network: string;
}> {
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

async function printBudget(amountUsd: string): Promise<void> {
  const amount = Number(amountUsd);
  if (!Number.isFinite(amount) || amount <= 0) {
    throw new Error('Budget amount must be a positive number.');
  }

  const pricing = await getPricing();
  const requests = Object.fromEntries(
    Object.entries(pricing.prices).map(([key, price]) => [key, Math.floor(amount / price)])
  );

  printJson({
    network: pricing.network,
    requests,
    source: pricing.source,
    token: pricing.token,
    usd: amount,
  });
}

const commands: Record<string, (args: ParsedArgs) => Promise<void>> = {
  async wallet(args) {
    const subcommand = args._[0] || 'help';

    if (subcommand === 'init') {
      const result = await initWallet();
      console.log(result.created ? 'Created payment wallet.' : 'Wallet already exists.');
      printJson({
        address: result.address,
        encrypted: result.encrypted,
        walletPath: result.walletPath,
      });
      console.log('Fund this Base address with USDC before making paid API calls.');
      return;
    }

<<<<<<< HEAD
    if (subcommand === 'migrate') {
      const result = await migrateWallet();
      console.log(
        result.migrated
          ? 'Migrated wallet to the managed storage path.'
          : 'Wallet already uses managed encrypted storage.'
      );
      printJson({
        address: result.address,
        encrypted: result.encrypted,
        moved: result.moved,
        sourceWalletPath: result.sourceWalletPath,
        walletPath: result.walletPath,
      });
      return;
    }

=======
>>>>>>> f76e1bf (refactor: move dao governance client to typescript)
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

<<<<<<< HEAD
    throw new Error('Usage: pnpm exec tsx degov-client.ts wallet <init|migrate|address|balance>');
=======
    throw new Error('Usage: pnpm exec tsx degov-client.ts wallet <init|address|balance>');
>>>>>>> f76e1bf (refactor: move dao governance client to typescript)
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
<<<<<<< HEAD
  wallet migrate                migrate legacy wallet into ~/.agents/state/dao-governance
=======
>>>>>>> f76e1bf (refactor: move dao governance client to typescript)
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
