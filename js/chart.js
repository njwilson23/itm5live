import {select, event, min, max, extent, line as d3line, map, scaleTime, scaleLinear, axisBottom, axisLeft} from "d3";
export {json, isoParse, zoom, d3mean};

// Create a set of axes for time series data
export function createTimeSeriesAxes(geom, id, label) {
  var ax = Object();

  var margin = geom.margin,
      width = geom.width,
      height = geom.height;

  // Define an original time scale to use when rescaling the actual time scale
  var x = scaleTime().range([0, width]),
      y = scaleLinear().range([height, 0]),
      x_orig = scaleTime().range([0, width]);

  var svg = select(id).append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom);

  var g = svg.append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var xDomain = [NaN, NaN],
      yDomain = [NaN, NaN];

  var xAxis = axisBottom(x),
      yAxis = axisLeft(y);

  var gX = g.append("g")
      .attr("class", "axis axis--x")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

  var gY = g.append("g")
      .attr("class", "axis axis--y")
      .call(yAxis);

  svg.append("text")
      .attr("class", "y label")
      .attr("x", -height-margin.top)
      .attr("y", 16)
      .attr("dy", ".75em")
      .attr("transform", "rotate(-90)")
      .text(label);

  svg.append("defs").append("clipPath")
        .attr("id", "clip")
      .append("rect")
        .attr("width", width)
        .attr("height", height);

  var zoomRect = g.append("rect")
    .attr("width", width)
    .attr("height", height)
    .attr("class", "plotArea");

  ax.xDomain = xDomain;
  ax.yDomain = yDomain;
  ax.margin = margin;
  ax.svg = svg;
  ax.g = g;
  ax.gX = gX;
  ax.gY = gY;
  ax.x = x;
  ax.y = y;
  ax.x_ = x_orig;
  ax.xAxis = xAxis;
  ax.yAxis = yAxis;
  ax.zoomRect = zoomRect;
  ax.series = map();
  return ax;
}

// Add scalar time series data to a set of axes
export function addScalarTimeSeries(ax, data, className) {
  var xExtent = extent(data, function(d) { return d.t; });

  if (isFinite(ax.xDomain[0])) {
    ax.xDomain[0] = Math.min(xExtent[0], ax.xDomain[0]);
  } else {
    ax.xDomain[0] = xExtent[0];
  }

  if (isFinite(ax.xDomain[1])) {
    ax.xDomain[1] = Math.max(xExtent[1], ax.xDomain[1]);
  } else {
    ax.xDomain[1] = xExtent[1];
  }

  ax.x.domain(ax.xDomain);
  ax.x_.domain(ax.xDomain);

  ax.gX.call(ax.xAxis);

  var line = d3line()
    .x(function(d) { return ax.x(d.t); })
    .y(function(d) { return ax.y(d.y); });

  var path = ax.g.append("path").datum(data)
    .attr("class", "line active " + className)
    .attr("d", line);

  ax.series.set(className, line);
  return {"path": path, "line": line};
}

// Add vector time series data to a set of axes
export function addVectorTimeSeries(ax, data, className) {
  var xExtent = extent(data, function(d) { return d.t; });

  if (isFinite(ax.xDomain[0])) {
    ax.xDomain[0] = Math.min(xExtent[0], ax.xDomain[0]);
  } else {
    ax.xDomain[0] = xExtent[0];
  }

  if (isFinite(ax.xDomain[1])) {
    ax.xDomain[1] = Math.max(xExtent[1], ax.xDomain[1]);
  } else {
    ax.xDomain[1] = xExtent[1];
  }

  ax.x.domain(ax.xDomain);
  ax.x_.domain(ax.xDomain);

  ax.gX.call(ax.xAxis);

  var g = ax.g.append("g").attr("class", "active " + className);

  var line = g.selectAll("line")
      .data(data);

  line.enter()
      .append("line")
      .attr("x1", function(d) { return ax.x(d.t) })
      .attr("y1", function(d) { return ax.y(d.y) })
      .attr("x2", function(d) { return ax.x(d.t)+d.vx })
      .attr("y2", function(d) { return ax.y(d.y)-d.vy })
      .attr("class", "vec "+className)
    .merge(line);

  var circle = g.selectAll("circle")
      .data(data);

  circle.enter().append("circle")
      .attr("cx", function(d) {return ax.x(d.t)})
      .attr("cy", function(d) {return ax.y(d.y)})
      .attr("r", 1.8)
      .attr("class", "vec active "+className)
    .merge(circle);
}

// Adjust the Y-scale on an axes to match the limits of active scalar data
export function tightenScaY(ax) {
  var data = ax.g.selectAll("path.active").data()
  var vmin = null, vmax = null;
  var _vmin, _vmax;
  for (var i=0; i!=data.length; i++) {
    _vmin = min(data[i], function(d) { return d.y; })
    _vmax = max(data[i], function(d) { return d.y; })
    vmin = vmin === null ? _vmin : Math.min(_vmin, vmin);
    vmax = vmax === null ? _vmax : Math.max(_vmax, vmax);
  }
  ax.yDomain[0] = vmin;
  ax.yDomain[1] = vmax;
  ax.y.domain(ax.yDomain);
  ax.gY.call(ax.yAxis.scale(ax.y));

  ax.g.selectAll("path.active").attr("d", ax.series.values()[0]);
}

// Adjust the Y-scale on an axes to match the limits of active vector data
export function tightenVecY(ax) {
  var data = ax.g.selectAll("circle.active").data()
  ax.yDomain[0] = Math.max(0, min(data, function(d) { return d.y-1; }));
  ax.yDomain[1] = max(data, function(d) { return d.y+1; });
  ax.y.domain(ax.yDomain);
  ax.gY.call(ax.yAxis.scale(ax.y));

  ax.g.selectAll("circle.vec")
    .attr("cy", function(d) {
      return ax.y(d.y);
    });

  ax.g.selectAll("line.vec")
    .attr("y1", function(d) {
      return ax.y(d.y);
    })
    .attr("y2", function(d) {
      var v = normalizeVec(100*d.east, 100*d.north);
      return ax.y(d.y)+d.vy;
    });
}

// Adjust the horizontal coodinates of data to match axes scales
export function rescaleAxes(ax) {
  ax.g.selectAll(".line")
    .attr("d", ax.series.values()[0]);

  ax.g.selectAll("circle.vec")
    .attr("cx", function(d) {
      return ax.x(d.t);
    });

  ax.g.selectAll("line.vec")
    .attr("x1", function(d) {
      return ax.x(d.t);
    })
    .attr("x2", function(d) {
      var v = normalizeVec(100*d.east, 100*d.north);
      return ax.x(d.t)+d.vx;
    });
}

export function zoomed() {
  var ax, t = event.transform;
  for (var i=0; i!=axes.length; i++) {
    ax = axes[i];
    ax.x.domain(t.rescaleX(ax.x_).domain());
    ax.gX.call(ax.xAxis.scale(ax.x));
    rescaleAxes(ax);
  }
}

// Filter function that detects rows in data with any nulls
export function filterNulls(d) {
  var k = Object.keys(d);
  for (var i=0; i!=k.length; i++) {
      if (d[k[i]] === null) {
      return false;
      }
  }
  return true;
}

// Compute the magnitude and unit vector of a vector
export function normalizeVec(u, v) {
      var mag = Math.sqrt(u*u + v*v);
      if (mag == 0) {
          return {mag: mag, u: 0, v: 0};
      } else {
          return {mag: mag, u: u/mag, v: v/mag};
      }
}

// Given an object containing arrays mapped to column names, return an Array containing row objects
// If the columns are of unequal length, pad the shorter ones with null
export function transpose(obj) {
  var properties = Object.keys(obj);
  var outArr = Array();
  var L = 0;
  var prop;
  for (var k=0; k!=properties.length; k++) {
    L = Math.max(obj[properties[k]].length);
  }
  for (var i=0; i!=L; i++) {
    var row = Object();
    for (var k=0; k!=properties.length; k++) {
      prop = properties[k]
      if (obj[prop].length > i) {
        row[prop] = obj[properties[k]][i];
      } else {
        row[prop] = null;
      }
    }
    outArr.push(row);
  }
  return outArr;
}