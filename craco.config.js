const path = require('path');

module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Remove any PWA/Workbox plugins
      webpackConfig.plugins = webpackConfig.plugins.filter(plugin => {
        return !plugin.constructor.name.includes('WorkboxWebpackPlugin') &&
               !plugin.constructor.name.includes('GenerateSW') &&
               !plugin.constructor.name.includes('InjectManifest');
      });

      // Remove manifest generation
      webpackConfig.plugins = webpackConfig.plugins.filter(plugin => {
        return !plugin.constructor.name.includes('WebpackManifestPlugin');
      });

      return webpackConfig;
    },
  },
};