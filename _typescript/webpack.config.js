const path = require('path');

module.exports = {
  mode: 'production',
  entry: {
    main: './_typescript/src/main.ts',
    'password-verification': './_typescript/src/password-verification.ts'
  },
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
