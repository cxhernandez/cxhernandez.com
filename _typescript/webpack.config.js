const path = require('path');
const { execSync } = require('child_process');
const webpack = require('webpack');

// Generate password hash from environment variable at build time
// Returns null if no password is set (allows open access to store)
function getPasswordHash() {
  try {
    const output = execSync('npx ts-node --project _typescript/tsconfig.scripts.json _typescript/generate-password-hash.ts', {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'inherit'], // Only capture stdout, show stderr (warnings)
    }).trim();
    return JSON.parse(output); // Returns hash string or null
  } catch (error) {
    console.error('Failed to generate password hash');
    throw error;
  }
}

// Encode store content to Base64 for obfuscation at build time
function getEncodedStoreContent() {
  try {
    const output = execSync('npx ts-node --project _typescript/tsconfig.scripts.json _typescript/encode-store-content.ts', {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'inherit'],
    }).trim();
    return JSON.parse(output); // Returns Base64 encoded string
  } catch (error) {
    console.error('Failed to encode store content');
    throw error;
  }
}

module.exports = {
  mode: 'production',
  entry: {
    main: './_typescript/src/main.ts',
    'password-verification': './_typescript/src/password-verification.ts'
  },
  plugins: [
    new webpack.DefinePlugin({
      'process.env.STORE_PASSWORD_HASH': JSON.stringify(getPasswordHash()),
      'process.env.STORE_CONTENT_ENCODED': JSON.stringify(getEncodedStoreContent()),
    }),
  ],
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  output: {
    filename: '[name].bundle.js',
    path: path.resolve(__dirname, '../static/js/dist'),
    clean: true,
  },
  externals: {
    // jQuery is loaded globally from CDN
    jquery: 'jQuery',
    // Bootstrap is loaded globally from CDN
    bootstrap: 'bootstrap',
    // Bootbox is loaded globally from CDN
    bootbox: 'bootbox'
  },
  devtool: 'source-map',
  optimization: {
    minimize: true,
  },
};
