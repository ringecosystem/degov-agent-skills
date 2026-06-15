import { isAddress, parseUnits } from 'viem';

export function parseTransferRecipient(value: string): `0x${string}` {
  const trimmed = value.trim();
  if (!isAddress(trimmed)) {
    throw new Error('Transfer destination must be a valid EVM address.');
  }
  return trimmed as `0x${string}`;
}

export function parseUsdcTransferAmount(value: string): bigint {
  const trimmed = value.trim();
  if (!/^\d+(?:\.\d{1,6})?$/.test(trimmed)) {
    throw new Error('Transfer amount must be a positive USDC amount with up to 6 decimal places.');
  }

  const amount = parseUnits(trimmed, 6);
  if (amount <= 0n) {
    throw new Error('Transfer amount must be a positive USDC amount.');
  }
  return amount;
}
