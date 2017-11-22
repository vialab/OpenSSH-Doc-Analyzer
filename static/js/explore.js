// maintain focus target
var focus_id = "";

// set the dimensions and margins of the vis
var margin = {top: 20, right: 90, bottom: 30, left: 90};
var padding = 15;
var min_size = 100;
var add_size = 50;
    
var format = d3.format(",d");

// color scale for depth
var color = d3.scaleLinear()
    .domain([0, 6])
    .range(["hsl(152,80%,80%)", "hsl(228,30%,40%)"])
    .interpolate(d3.interpolateHcl);

// hierarchical data conversion function from csv
var stratify = d3.stratify()
    .id(function(d) { return d.name; })
    .parentId(function(d) { return d.parent; });

function hovered(hover) {
    return function(d) {
        d3.selectAll(d.ancestors().map(function(d) { return d.name; })).classed("node--hover", hover);
    };
}

function clicked(cb_keyword) {
    return function(d) {
        d3.event.stopPropagation();
        if( d.data.keyword ) {
            cb_keyword(d);
            return;
        }
        var $container = $(this).closest("svg");
        var svg_id = $container.attr("id");
        var width = $container.attr("width");
        var height = $container.attr("height");
        var pack = d3.pack().size([width, height]).padding(padding);    
        update(d3.select("svg#" + svg_id), pack, "/oht/", d.id, true, true, true, d.data.heading_id, cb_keyword);
    };
}

function createNewVis(svg_path, svg_id, path, id, width, height, weight, change_focus=true, add_label=true, add_event=true, heading_id, cb_keyword) {
    svg_id = svg_id.replace(/\./g, "-");
    var svg = null;

    if($(svg_path + " #"+svg_id).length > 0) {
        svg = d3.select(svg_path + " #"+svg_id);
    } else {
        svg = d3.select(svg_path).append("svg");
        svg.append("g").attr("transform", "translate(2.5,2.5)");
    }

    svg.attr("width", width);
    svg.attr("height", height);
    svg.attr("weight", weight);
    svg.attr("id", svg_id);
    svg.attr("tier-index", id);
    
    var pack = d3.pack().size([width-5, height-5]).padding(padding);
    update(svg, pack, path, id, change_focus, add_label, add_event, heading_id, cb_keyword);
}

function update(svg, pack, path, id, change_focus=true, add_label=true, add_event=true, heading_id, cb_keyword) {
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
            .each(function(d) { d.name = this; });

        if(add_event) {
            node.on("mouseover", hovered(true))
            .on("mouseout", hovered(false))
            .on("click", clicked(cb_keyword));
        }

        node.append("circle")
        .attr("id", function(d) { return "node-" + d.data.heading_id; })
        .attr("r", function(d) { return d.r; })
        .style("fill", function(d) { 
            if(d.data.keyword) {
                if(d.data.heading_id == heading_id) {                    
                    return "rgb(255,0,0)";
                } else {
                    return color(-4);
                }
            } else {
                return color(d.depth);                
            }
        });
        if(add_label) {
            var leaf = node.filter(function(d) { return !d.children; });
        
            leaf.append("clipPath")
                .attr("id", function(d) { return "clip-" + d.data.heading_id; })
            .append("use")
                .attr("xlink:href", function(d) { return "#node-" + d.data.heading_id + ""; });
        
            leaf.append("text")
                .attr("clip-path", function(d) { return "url(#clip-" + d.data.heading_id + ")"; })
            .selectAll("tspan")
            .data(function(d) { return d.id.split(/(?=[A-Z][^A-Z])/g); })
            .enter().append("tspan")
                .attr("x", 0)
                .attr("y", function(d, i, nodes) { return 13 + (i - nodes.length / 2 - 0.5) * 10; })
                .text(function(d) { return d; });
        
            node.append("title")
                .text(function(d) { return d.id; });
        }
        
        if(change_focus) {
            focus_id = id;            
        }
    });
}

function collapse(d) {
    if (d.children) {
        d._children = d.children;
        d._children.forEach(collapse);
        d.children = null;
    }
}

function drawSearchTerm(tier_index, heading_id, heading_text, weight) {
    tier_id = tier_index.replace(/\./g, "-");
    var container_path = "term-" + tier_id;
    container_path += "-" + $("[id^=" + container_path + "]").length.toString();
    var svg_path = "term-vis-" + tier_id;
    svg_path += "-" + $("[id^=" + svg_path + "]").length.toString();
    var $box = $("<div class='term-container text-center' id='"
        + container_path + "'><button class='close' onclick='$(this).parent().remove();'>\
        <span>&times;</span></button><input type='hidden' class='term-heading-id' value='" 
        + heading_id +"'/><input type='hidden' class='term-heading-weight' value='1'/>\
        <div class='term-heading'>" + heading_text + "</div><div class='term-vis' id='" 
        + svg_path + "'></div></div>");
    
    $("#add-term").before($box);
    var vis_size = min_size + (add_size * weight);
    
    svg_path = "#" + svg_path;

    createNewVis(svg_path, "mini-" + tier_id
        , "/oht/", tier_index, vis_size, vis_size, weight, false, false, false, heading_id);
}