const path = require('path');
const { execSync } = require('child_process');
const webpack = require('webpack');

// Generate password hash from environment variable at build time
// Returns null if no password is set (allows open access to store)
function getPasswordHash() {
  try {
    const output = execSync('node _typescript/generate-password-hash.js', {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'inherit'], // Only capture stdout, show stderr (warnings)
    }).trim();
    return JSON.parse(output); // Returns hash string or null
  } catch (error) {
    console.error('Failed to generate password hash');
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
