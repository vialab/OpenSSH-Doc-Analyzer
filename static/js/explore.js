// maintain focus target
var focus_id = "";

// set the dimensions and margins of the vis
var margin = {top: 20, right: 90, bottom: 30, left: 90};
var padding = 30;
var min_size = 100;
var add_size = 50;
    
var format = d3.format(",d");

// hierarchical data conversion function from csv
var stratify = d3.stratify()
    .id(function(d) { return d.heading_id; })
    .parentId(function(d) { return d.parent; });

// queue of visualizations to request
var hook_busy = false;
var vis_queue = [];

// color scale for depth
var world_color = d3.scaleLinear()
    .domain([-2, 6])
    .range(["hsl(132,80%,80%)", "hsl(202,30%,40%)"])
    .interpolate(d3.interpolateHcl);
var mind_color = d3.scaleLinear()
    .domain([-2, 6])
    .range(["hsl(182,80%,80%)", "hsl(252,30%,40%)"])
    .interpolate(d3.interpolateHcl);
var society_color = d3.scaleLinear()
    .domain([-2, 6])
    .range(["hsl(212,80%,80%)", "hsl(302,30%,40%)"])
    .interpolate(d3.interpolateHcl);
var default_color = d3.scaleLinear()
    .domain([0, 1])
    .range(["#fff", "#fff"])
    .interpolate(d3.interpolateHcl);

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
        // var pack = d3.pack().size([width, height]).padding(padding);  
        var pack = d3.treemap()
        .size([width, height])
        .paddingOuter(padding)
        .tile(d3.treemapBinary);
        
        // update the circle pack to show new tier
        update(d3.select("svg#" + svg_id), pack, "/oht/", d.id, true
            , true, true, d.data.heading_id, cb_keyword);
    };
}

// create a circle pack vis at a designated DOM path
// args:
// svg_path - path to the parent where SVG is to exist
// svg_id   - id of the svg
// path     - base URL for data requet
// id       - tier-index
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
        svg.append("g").attr("transform", "translate(0,0)");
    }
    
    // set svg attributes
    svg.attr("width", width);
    svg.attr("height", height);
    svg.attr("weight", weight);
    svg.attr("id", svg_id);
    svg.attr("tier-index", id);
    
    // var pack = d3.pack().size([width-5, height-5]).padding(padding);
    var pack = d3.treemap()
    .size([width, height])
    .paddingOuter(padding)
    .tile(d3.treemapBinary);

    
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
            .sum(function(d) { return 10; });
    
        // assign the name to each node
        root.each(function(d) {
            d.name = d.id;
        });
        // convert hierarchy data to circle pack data
        pack(root);
        // clear all previous data nodes
        var node = svg.select("g")
        .selectAll("g").remove();
        console.log(root.descendants());
        // create new data nodes to svg
        node = svg.select("g")
        .selectAll("g")
        .data(root.descendants())
        .enter().append("g")
            .attr("transform", function(d) { return "translate(" + [d.x0, d.y0] + ")"; })
            .attr("tier-index", function(d) { return d.data.parent; })
            .each(function(d) { d.name = this; });
            
        // add click events if required
        if(add_event) {
            node.on("mouseover", hovered(true))
            .on("mouseout", hovered(false))
            .on("click", clicked(cb_keyword));
        }


        // draw the rectangles 
        node.append("rect")
        .attr("id", function(d) { return d.data.id; })
        .attr("width", function(d) { return d.x1 - d.x0; })
        .attr("height", function(d) { return d.y1 - d.y0; })
        .attr("fill", function(d) { return getColor(d); })
        .style("stroke", "rgb(0,0,0)")
        .style("stroke-width", 1);

        // draw labels to nodes if we need to
        if(add_label) {
            // var leaf = node.filter(function(d) { return d.data.keyword; });
        //     leaf.append("clipPath")
        //     .attr("id", function(d) { return "clip-" + d.data.heading_id; })
        //   .append("use")
        //     .attr("xlink:href", function(d) { return "#" + d.data.heading_id; });
      
            node.append("text")
                .text(function(d) { 
                    if(d.data.keyword == "") {
                        return d.data.th.split(/(?=[A-Z][^A-Z])/g)
                    }
                    return d.data.name.split(/(?=[A-Z][^A-Z])/g); 
                })
                .attr("dx", function(d) { return 5; })
                .attr("dy", function(d) { return 15; })
                .attr("box-width", function(d) {
                    return d.x1 - d.x0;
                })
                .style("fill", function(d) {
                    if(d.data.keyword != "") {
                        return default_color(0);
                    }
                })
                .call(wrap);

            // add a title for when a node is hovered
            node.append("title")
                .text(function(d) {                     
                    if(d.data.keyword == "") {
                        return d.data.th.split(/(?=[A-Z][^A-Z])/g);
                    }
                    return d.data.name.split(/(?=[A-Z][^A-Z])/g);
                }
            );
        }
        
        // record change of tier index
        if(change_focus) {
            focus_id = id;            
        }

        processNextUpdateRequest();
    });
}

function wrap(text) {
    text.each(function() {
        var text = d3.select(this),
            words = text.text().trim().split(/[\s\/\\]+/).reverse(),
            word,
            line = [],
            lineNumber = 0,
            lineHeight = 1.5, // ems
            dy = text.attr("dy"),
            dx = text.attr("dx"),
            em = 1.2,
            width = text.attr("box-width")-padding,
            tspan = text.text(null).append("tspan").attr("x", 0).attr("dy", lineHeight + "em");
        while (word = words.pop()) {
            line.push(word);
            tspan.text(line.join(" "));
            if (tspan.node().getComputedTextLength() > width) {
                line.pop();
                tspan.text(line.join(" "));
                line = [word];
                tspan = text.append("tspan").attr("x", 5).attr("y", y).attr("dy", ++lineNumber * lineHeight + em + "em").text(word);
            }
        }
    });
}

function processNextUpdateRequest() {
    if(vis_queue.length > 0) {
        var temp = vis_queue.pop();
        update(temp.svg, temp.pack, temp.path, temp.id, temp.change_focus
            , temp.add_label, temp.add_event, temp.heading_id
            , temp.cb_keyword);
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
    // color scale for depth
    var color = d3.scaleLinear()
        .domain([0, 6])
        .range(["hsl(152,80%,80%)", "hsl(228,30%,40%)"])
        .interpolate(d3.interpolateHcl);
    // draw mini-vis to this element
    createNewVis(svg_path, "mini-" + tier_id
        , "/oht/", tier_index, vis_size, vis_size, weight, false, false
        , false, heading_id, color);
    
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

function getColor(d) {
    let category = 0;
    if(typeof(d.data.cat) != "undefined") {
        category = parseInt(d.data.cat);
    }

    if($("#modal-heading-id").val() == d.data.heading_id) {
        return default_color(0);
    }

    switch(category) {
        case 2: // the mind
            return mind_color(d.data.tier);
            break;
        case 3: // society
            return society_color(d.data.tier);
            break;
        case 1: // the world
            return world_color(d.data.tier);
            break;
        default:
            return default_color(d.data.tier);
            break;
    }
}