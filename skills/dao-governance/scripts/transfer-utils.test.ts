import assert from 'node:assert/strict';
import test from 'node:test';
import { parseUsdcTransferAmount, parseTransferRecipient } from './transfer-utils.js';

test('parseTransferRecipient accepts a valid EVM address', () => {
  const address = '0x000000000000000000000000000000000000dEaD';

  assert.equal(parseTransferRecipient(address), address);
});

test('parseTransferRecipient rejects invalid destination addresses', () => {
  assert.throws(() => parseTransferRecipient('not-an-address'), /valid EVM address/);
});

test('parseUsdcTransferAmount converts decimal USDC into base units', () => {
  assert.equal(parseUsdcTransferAmount('1.234567'), 1234567n);
});

test('parseUsdcTransferAmount rejects zero, negative, and over-precision amounts', () => {
  assert.throws(() => parseUsdcTransferAmount('0'), /positive USDC amount/);
  assert.throws(() => parseUsdcTransferAmount('-1'), /positive USDC amount/);
  assert.throws(() => parseUsdcTransferAmount('0.0000001'), /up to 6 decimal places/);
});
