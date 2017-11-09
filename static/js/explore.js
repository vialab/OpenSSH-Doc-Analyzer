// maintain focus target
var focus_id = "1.NA.NA.NA.NA.NA.NA.1"; 

// set the dimensions and margins of the diagram
var margin = {top: 20, right: 90, bottom: 30, left: 90},
width = 900 - margin.left - margin.right,
height = 900 - margin.top - margin.bottom;

var svg = d3.select("svg"),
    width = +svg.attr("width"),
    height = +svg.attr("height");
    
var format = d3.format(",d");

// var color = d3.scaleSequential(d3.interpolateMagma)
//     .domain([-4, 4]);

var color = d3.scaleLinear()
    .domain([0, 6])
    .range(["hsl(152,80%,80%)", "hsl(228,30%,40%)"])
    .interpolate(d3.interpolateHcl);

var pack = d3.pack()
    .size([width, height])
    .padding(15);

var stratify = d3.stratify()
    .id(function(d) { return d.name; })
    .parentId(function(d) { return d.parent; });

update("/oht/1.NA.NA.NA.NA.NA.NA.1");

function hovered(hover) {
    return function(d) {
        d3.selectAll(d.ancestors().map(function(d) { return d.name; })).classed("node--hover", hover);
    };
}

function clicked() {
    return function(d) {
        if( d.data.keyword ) {
            return;
        }
        switch(d.depth) {
            case 0: // expand this level
            case 2:
                update("/oht/", d.id);
                break;
            case 3: // expand this level's parent
                update("/oht/", d.parent.id);
                break;
            case 4: // select keyword
                break;
            case 1: // don't do anything
            default:
                break;
        }
    };
}

function update(path, id) {
    if(focus_id == id) {
        return;
    }

    var url_path = path + id;
    d3.csv(url_path, function(error, data) {
        if (error) throw error;
        
        // convert the flat data into a hierarchy 
        var root = stratify(data)
            .sum(function(d) { return d.size });
    
        // assign the name to each node
        root.each(function(d) {
            d.name = d.id;
        });

        pack(root);

        var node = svg.select("g")
        .selectAll("g").remove();

        node = svg.select("g")
        .selectAll("g")
        .data(root.descendants())
        .enter().append("g")
            .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
            .attr("class", function(d) { return "node" + (!d.children ? " node--leaf" : d.depth ? "" : " node--root"); })
            .each(function(d) { d.name = this; })
            .on("mouseover", hovered(true))
            .on("mouseout", hovered(false))
            .on("click", clicked());

        node.append("circle")
        .attr("id", function(d) { return "node-" + d.id; })
        .attr("r", function(d) { return d.r; })
        .style("fill", function(d) { 
            if(d.data.keyword) {
                return color(-4);
            } else {
                return color(d.depth);                
            }
        });
    
        var leaf = node.filter(function(d) { return !d.children; });
    
        leaf.append("clipPath")
            .attr("id", function(d) { return "clip-" + d.id; })
        .append("use")
            .attr("xlink:href", function(d) { return "#node-" + d.id + ""; });
    
        leaf.append("text")
            .attr("clip-path", function(d) { return "url(#clip-" + d.id + ")"; })
        .selectAll("tspan")
        .data(function(d) { return d.id.split(/(?=[A-Z][^A-Z])/g); })
        .enter().append("tspan")
            .attr("x", 0)
            .attr("y", function(d, i, nodes) { return 13 + (i - nodes.length / 2 - 0.5) * 10; })
            .text(function(d) { return d; });
    
        node.append("title")
            .text(function(d) { return d.id; });

        focus_id = id;
    });
}

function collapse(d) {
    if (d.children) {
        d._children = d.children;
        d._children.forEach(collapse);
        d.children = null;
    }
}