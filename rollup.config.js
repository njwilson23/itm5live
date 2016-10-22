import nodeResolve from "rollup-plugin-node-resolve";

export default {
  entry: 'js/itm5live.package.js',
  dest: 'js/itm5live.js',
  format: 'iife',
  moduleName: 'itm',
  plugins: [nodeResolve({ jsnext: true, main: true })]
};
