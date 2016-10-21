import nodeResolve from "rollup-plugin-node-resolve";

export default {
  entry: 'js/chart.js',
  dest: 'js/itm5live.js',
  format: 'iife',
  moduleName: 'itm5live',
  plugins: [nodeResolve({ jsnext: true, main: true })]
};
