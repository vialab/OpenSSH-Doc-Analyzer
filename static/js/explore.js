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

// queue of visualizations to request
var hook_busy = false;
var vis_queue = [];

// draw outline on hovered circled and its ancestors
function hovered(hover) {
    return function(d) {
        d3.selectAll(d.ancestors().map(function(d) { return d.name; }))
            .classed("node--hover", hover);
    };
}

// default function for a clicked circle node
function clicked(cb_keyword) {
    return function(d) {
        d3.event.stopPropagation();
        if( d.data.keyword ) {
            // if we clicked a keyword
            // run the callback function
            cb_keyword(d);
            return;
        }
        // otherwise we clicked another tier
        var $container = $(this).closest("svg");
        var svg_id = $container.attr("id");
        var width = $container.attr("width");
        var height = $container.attr("height");
        var pack = d3.pack().size([width, height]).padding(padding);  
        
        // update the circle pack to show new tier
        update(d3.select("svg#" + svg_id), pack, "/oht/", d.id, true
            , true, true, d.data.heading_id, cb_keyword);
    };
}

// create a circle pack vis at a designated DOM path
function createNewVis(svg_path, svg_id, path, id, width, height, weight
                    , change_focus=true, add_label=true, add_event=true, heading_id
                    , cb_keyword) {
    svg_id = svg_id.replace(/\./g, "-");
    var svg = null;
    if($(svg_path + " #"+svg_id).length > 0) {
        // if path exists, select the svg that is there
        svg = d3.select(svg_path + " #"+svg_id);
    } else {
        // otherwise, append an SVG to path
        svg = d3.select(svg_path).append("svg");
        svg.append("g").attr("transform", "translate(2.5,2.5)");
    }
    
    // set svg attributes
    svg.attr("width", width);
    svg.attr("height", height);
    svg.attr("weight", weight);
    svg.attr("id", svg_id);
    svg.attr("tier-index", id);
    
    var pack = d3.pack().size([width-5, height-5]).padding(padding);
    
    if(hook_busy) {
        // queue this request and wait for others to finish first
        var temp = {
            "svg":svg
            , "pack":pack
            , "path":path
            , "id":id
            , "change_focus":change_focus
            , "add_label":add_label
            , "add_event":add_event
            , "heading_id":heading_id
            , "cb_keyword":cb_keyword
        }
        vis_queue.push(temp);
    } else {
        // draw the circle pack
        update(svg, pack, path, id, change_focus, add_label, add_event
            , heading_id, cb_keyword);
    }
}

// update a vis with new tier index
function update(svg, pack, path, id, change_focus=true, add_label=true
                , add_event=true, heading_id, cb_keyword) {

    var url_path = path + id;
    hook_busy = true;
    // get the new tier nodes from the server
    d3.csv(url_path, function(error, data) {
        if (error) throw error;
        
        // convert the flat data into a hierarchy 
        var root = stratify(data)
            .sum(function(d) { return d.size });
    
        // assign the name to each node
        root.each(function(d) {
            d.name = d.id;
        });
        // convert hierarchy data to circle pack data
        pack(root);

        // clear all previous data nodes
        var node = svg.select("g")
        .selectAll("g").remove();
        
        // create new data nodes to svg
        node = svg.select("g")
        .selectAll("g")
        .data(root.descendants())
        .enter().append("g")
            .attr("transform", function(d) { return "translate(" + d.x + "," 
                + d.y + ")"; })
            .attr("class", function(d) { 
                return "node" 
                    + (!d.children ? " node--leaf" 
                        : d.depth ? "" : " node--root"); })
            .each(function(d) { d.name = this; });
            
        // add click events if required
        if(add_event) {
            node.on("mouseover", hovered(true))
            .on("mouseout", hovered(false))
            .on("click", clicked(cb_keyword));
        }

        // draw the circles
        node.append("circle")
        .attr("id", function(d) { return "node-" + d.data.heading_id; })
        .attr("r", function(d) { return d.r; })
        .style("fill", function(d) { 
            if(d.data.keyword) {
                // fill keywords with white
                if(d.data.heading_id == heading_id) {                    
                    return "rgb(0,100,150)";
                } else {
                    return color(-4);
                }
            } else {
                // otherwise use linear color scale based on depth
                return color(d.depth);                
            }
        });

        // draw labels to nodes if we need to
        if(add_label) {
            var leaf = node.filter(function(d) { return !d.children; });
            // clip text to stay inside of circle
            leaf.append("clipPath")
                .attr("id", function(d) { return "clip-" + d.data.heading_id; })
            .append("use")
                .attr("xlink:href", function(d) { return "#node-" 
                    + d.data.heading_id + ""; });
            
                    // add the text in the clip path
            leaf.append("text")
                .attr("clip-path", function(d) { return "url(#clip-" 
                    + d.data.heading_id + ")"; })
            .selectAll("tspan")
            .data(function(d) { return d.id.split(/(?=[A-Z][^A-Z])/g); })
            .enter().append("tspan")
                .attr("x", 0)
                .attr("y", function(d, i, nodes) { return 13 
                    + (i - nodes.length / 2 - 0.5) * 10; })
                .text(function(d) { return d; });
            
            // add a title for when a node is hovered
            node.append("title")
                .text(function(d) { return d.id; });
        }
        
        // record change of tier index
        if(change_focus) {
            focus_id = id;            
        }

        processNextUpdateRequest();
    });
}

function processNextUpdateRequest() {
    if(vis_queue.length > 0) {
        var temp = vis_queue.pop();
        update(temp.svg, temp.pack, temp.path, temp.id, temp.change_focus
            , temp.add_label, temp.add_event, temp.heading_id, temp.cb_keyword);
    } else {
        hook_busy = false;
    }
}

// don't show children nodes but save them as meta info
function collapse(d) {
    if (d.children) {
        d._children = d.children;
        d._children.forEach(collapse);
        d.children = null;
    }
}

// draw a search term to the DOM with included mini-vis
function drawSearchTerm(tier_index, heading_id, heading_text, weight) {
    tier_id = tier_index.replace(/\./g, "-");
    var container_path = "term-" + tier_id;
    container_path += "-" + $("[id^=" + container_path + "]").length.toString();
    var svg_path = "term-vis-" + tier_id;
    svg_path += "-" + $("[id^=" + svg_path + "]").length.toString();
    
    // search term html
    var $box = $("<div class='term-container text-center' id='"
        + container_path + "'><button class='close' onclick='deleteTerm(this);'>\
        <span>&times;</span></button><input type='hidden' class='term-heading-id' value='" 
        + heading_id +"'/><input type='hidden' class='term-heading-weight' value='1'/>\
        <div class='term-heading'>" + heading_text + "</div><div class='term-vis' id='" 
        + svg_path + "'></div></div>");
    
    // prepend before add term button
    $("#add-term").before($box);
    var vis_size = min_size + (add_size * weight);
    
    svg_path = "#" + svg_path;

    // draw mini-vis to this element
    createNewVis(svg_path, "mini-" + tier_id
        , "/oht/", tier_index, vis_size, vis_size, weight, false, false, false, heading_id);
    
    // re-instantiate sortable (drag and drop) dom elements
    resortable();
}

function drawKeyword(keyword) {
    var $box = $("<div class='term-container text-center custom-keyword' id='keyword-"
    + (new Date()).getTime() + "'><button class='close' onclick='deleteTerm(this);'>\
    <span>&times;</span></button><input type='hidden' class='custom-keyword-weight' value='1'/>\
    <div class='custom-keyword-heading'>" + keyword + "</div></div>");
    $("#add-term").before($box);    
    resortable();    
}

function resortable() {
    // re-instantiate sortable (drag and drop) dom elements
    $("#search-term-box").sortable("destroy");
    $("#search-term-box").sortable({
        items: ".term-container"
    });
}