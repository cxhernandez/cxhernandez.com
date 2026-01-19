#!/usr/bin/env node

/**
 * Generates a SHA-256 hash from the STORE_PASSWORD environment variable.
 * This hash is injected into the webpack build at compile time.
 *
 * Usage:
 *   STORE_PASSWORD="mypassword" node generate-password-hash.js
 *
 * Returns the hash as a JSON string for use in webpack DefinePlugin.
 */

const crypto = require('crypto');

function generatePasswordHash() {
  const password = process.env.STORE_PASSWORD;

  if (!password) {
    console.warn('');
    console.warn('⚠️  WARNING: STORE_PASSWORD environment variable is not set');
    console.warn('⚠️  Store will be accessible WITHOUT password protection');
    console.warn('⚠️  Set STORE_PASSWORD in GitHub Secrets or local environment for production');
    console.warn('');
    return null;
  }

  // Generate SHA-256 hash
  const hash = crypto
    .createHash('sha256')
    .update(password)
    .digest('hex');

  return hash;
}

// Generate hash and output as JSON string for webpack
const hash = generatePasswordHash();
console.log(JSON.stringify(hash));
