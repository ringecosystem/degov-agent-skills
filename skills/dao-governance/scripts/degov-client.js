#!/usr/bin/env node

const { wrapFetchWithPaymentFromConfig } = require('@x402/fetch');
const { ExactEvmScheme, toClientEvmSigner } = require('@x402/evm');
const { createPublicClient, http } = require('viem');
const { base } = require('viem/chains');
const {
  DEFAULT_WALLET_PATH,
  getAccount,
  getUsdcBalance,
  getWalletPath,
  initWallet,
} = require('./wallet-store');

const API_BASE_URL = process.env.DEGOV_AGENT_API_BASE_URL || 'http://127.0.0.1:3310';

const PRICES = {
  daos: 0.005,
  activity: 0.005,
  freshness: 0.005,
  brief: 0.02,
  item: 0.02,
};

function parseArgs() {
  const args = { _: [] };
  for (let i = 2; i < process.argv.length; i += 1) {
    const arg = process.argv[i];
    if (arg.startsWith('--')) {
      const next = process.argv[i + 1];
      if (next && !next.startsWith('--')) {
        args[arg] = next;
        i += 1;
      } else {
        args[arg] = true;
      }
    } else {
      args._.push(arg);
    }
  }
  return args;
}

function getPaymentClient() {
  const { account } = getAccount();
  const publicClient = createPublicClient({
    chain: base,
    transport: http('https://mainnet.base.org'),
  });
  const signer = toClientEvmSigner(account, publicClient);

  return {
    account,
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

async function apiCall(endpoint) {
  const { account, fetchWithPayment } = getPaymentClient();
  const url = `${API_BASE_URL}${endpoint}`;

  console.error(`Using wallet: ${account.address}`);
  console.error(`Calling: ${url}`);

  const response = await fetchWithPayment(url);
  const text = await response.text();

  let payload;
  try {
    payload = JSON.parse(text);
  } catch {
    payload = text;
  }

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${typeof payload === 'string' ? payload : JSON.stringify(payload)}`);
  }

  return payload;
}

function printJson(value) {
  console.log(JSON.stringify(value, null, 2));
}

function printBudget(amountUsd) {
  const amount = Number(amountUsd);
  if (!Number.isFinite(amount) || amount <= 0) {
    throw new Error('Budget amount must be a positive number.');
  }

  const output = Object.fromEntries(
    Object.entries(PRICES).map(([key, price]) => [key, Math.floor(amount / price)])
  );

  printJson({
    usd: amount,
    requests: output,
  });
}

const commands = {
  async wallet(args) {
    const subcommand = args._[0] || 'help';

    if (subcommand === 'init') {
      const result = initWallet();
      console.log(result.created ? 'Created payment wallet.' : 'Wallet already exists.');
      printJson({
        address: result.address,
        walletPath: result.walletPath,
      });
      console.log('Fund this Base address with USDC before making paid API calls.');
      return;
    }

    if (subcommand === 'address') {
      const { account, walletPath } = getAccount();
      printJson({
        address: account.address,
        walletPath,
      });
      return;
    }

    if (subcommand === 'balance') {
      const { account, walletPath } = getAccount();
      const balance = await getUsdcBalance(account.address);
      printJson({
        address: account.address,
        walletPath,
        network: 'Base Mainnet',
        asset: 'USDC',
        balance: balance.formatted,
        raw: balance.raw.toString(),
      });
      return;
    }

    throw new Error('Usage: node degov-client.js wallet <init|address|balance>');
  },

  async budget(args) {
    printBudget(args['--usd'] || '1');
  },

  async daos() {
    const data = await apiCall('/v1/daos');
    printJson(data);
  },

  async activity(args) {
    const params = new URLSearchParams();
    if (args['--dao']) params.set('dao_id', args['--dao']);
    if (args['--hours']) params.set('hours', args['--hours']);
    if (args['--limit']) params.set('limit', args['--limit']);
    if (args['--types']) params.set('types', args['--types']);
    if (args['--governance']) params.set('governance_only', 'true');
    const query = params.toString() ? `?${params.toString()}` : '';
    const data = await apiCall(`/v1/activity${query}`);
    printJson(data);
  },

  async brief(args) {
    const daoId = args._[0];
    if (!daoId) {
      throw new Error('Usage: node degov-client.js brief <dao-id> [--activity-limit N]');
    }

    const params = new URLSearchParams();
    if (args['--activity-limit']) params.set('activity_limit', args['--activity-limit']);
    const query = params.toString() ? `?${params.toString()}` : '';
    const data = await apiCall(`/v1/daos/${daoId}/brief${query}`);
    printJson(data);
  },

  async item(args) {
    const kind = args._[0];
    const externalId = args._[1];
    if (!kind || !externalId) {
      throw new Error('Usage: node degov-client.js item <proposal|forum_topic> <external-id>');
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
    const data = await response.json();
    printJson(data);
  },

  async help() {
    console.log(`DAO Governance Client

Wallet storage:
  ${DEFAULT_WALLET_PATH}

Environment:
  DEGOV_AGENT_API_BASE_URL   default ${API_BASE_URL}
  DEGOV_AGENT_WALLET_PATH    optional wallet file override

Commands:
  wallet init                create or reuse local payment wallet
  wallet address             show wallet address and path
  wallet balance             show Base USDC balance
  budget --usd 1             estimate requests per dollar
  daos                       list DAOs
  activity [--dao ens] [--hours 24] [--limit 10] [--types proposal,forum_topic] [--governance]
  brief <dao-id> [--activity-limit 6]
  item <proposal|forum_topic> <external-id>
  freshness
  health
  help
`);
  },
};

async function main() {
  const args = parseArgs();
  const command = args._[0] || 'help';
  args._.shift();

  const handler = commands[command];
  if (!handler) {
    throw new Error(`Unknown command: ${command}`);
  }

  await handler(args);
}

main().catch((error) => {
  console.error(error.message || String(error));
  process.exit(1);
});
