const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { privateKeyToAccount, generatePrivateKey } = require('viem/accounts');
const { createPublicClient, formatUnits, http, parseAbi } = require('viem');
const { base } = require('viem/chains');

const DEFAULT_WALLET_PATH = path.join(
  os.homedir(),
  '.codex',
  'memories',
  'degov-agent-skills',
  'dao-governance-wallet.json'
);

const USDC_ADDRESS = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
const USDC_ABI = parseAbi(['function balanceOf(address) view returns (uint256)']);

function getWalletPath() {
  return process.env.DEGOV_AGENT_WALLET_PATH || DEFAULT_WALLET_PATH;
}

function ensureWalletDir(walletPath) {
  fs.mkdirSync(path.dirname(walletPath), { recursive: true });
}

function writeWalletFile(walletPath, payload) {
  ensureWalletDir(walletPath);
  fs.writeFileSync(walletPath, `${JSON.stringify(payload, null, 2)}\n`, { mode: 0o600 });
}

function readWalletFile(walletPath = getWalletPath()) {
  if (!fs.existsSync(walletPath)) {
    return null;
  }

  return JSON.parse(fs.readFileSync(walletPath, 'utf8'));
}

function getAccount(walletPath = getWalletPath()) {
  const wallet = readWalletFile(walletPath);
  if (!wallet?.privateKey) {
    throw new Error(`Wallet not initialized. Run: node degov-client.js wallet init`);
  }

  return {
    walletPath,
    wallet,
    account: privateKeyToAccount(wallet.privateKey),
  };
}

function initWallet(walletPath = getWalletPath()) {
  const existing = readWalletFile(walletPath);
  if (existing?.privateKey && existing?.address) {
    return {
      walletPath,
      created: false,
      address: existing.address,
    };
  }

  const privateKey = generatePrivateKey();
  const account = privateKeyToAccount(privateKey);
  writeWalletFile(walletPath, {
    createdAt: new Date().toISOString(),
    address: account.address,
    privateKey,
  });

  return {
    walletPath,
    created: true,
    address: account.address,
  };
}

async function getUsdcBalance(address) {
  const publicClient = createPublicClient({
    chain: base,
    transport: http('https://mainnet.base.org'),
  });

  const balance = await publicClient.readContract({
    address: USDC_ADDRESS,
    abi: USDC_ABI,
    functionName: 'balanceOf',
    args: [address],
  });

  return {
    raw: balance,
    formatted: formatUnits(balance, 6),
  };
}

module.exports = {
  DEFAULT_WALLET_PATH,
  USDC_ADDRESS,
  getWalletPath,
  initWallet,
  getAccount,
  getUsdcBalance,
};
