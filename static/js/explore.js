// maintain focus target
var focus_id = "";

// set the dimensions and margins of the vis
var margin = {top: 20, right: 90, bottom: 30, left: 90};
var padding = 20;
var min_size = 100;
var add_size = 50;
var format = d3.format(",d");
var oneclick = false;
var click_to;
var chart_data;
// hierarchical data conversion function from csv
var stratify = d3.stratify()
    .id(function(d) { return d.heading_id; })
    .parentId(function(d) { return d.parent; });

// queue of visualizations to request
var hook_busy = false;
var vis_queue = [];
var journal_timeout;
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
    .range(["#fff", "#000"])
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
        d3.selectAll("g").style("stroke", "");
        if(!oneclick) {
            oneclick = true;
            var click_to = setTimeout(function() {
                if(oneclick) {
                    cb_keyword(d);
                }
                oneclick = false;
            }, 250);
            d3.select(this).style("stroke", "rgb(220,100,100)");            
        } else {
            oneclick = false;
            clearTimeout(click_to);
            if(d.data.length == "0") {
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
        }
    }
}


// create a barchart to display distribution
function drawJournalCount(data, merge) {
    let keys = ["freq"];
    let y_mean = 0;
    // append new query data to current if we have new search query
    // also calculate the mean for label filtering
    if(merge && typeof(chart_data) != "undefined") {
        let n = 0, sum = 0;
        for(var i = 0; i < chart_data.length; i++) {
            chart_data[i].new = data[i].freq;
            chart_data[i].total = data[i].freq + chart_data[i].freq;
            sum += chart_data[i].total;
            n += 2;
        }
        y_mean = sum / n;
        keys.push("new");
    } else {
        // not appending, but we still want to calculate the mean
        chart_data = data;
        let n = 0, sum = 0;
        for(var i = 0; i < chart_data.length; i++) {
            chart_data[i].total = chart_data[i].freq;
            sum += chart_data[i].total;
            n += 1;
        }
        y_mean = sum / n;        
    }
    // start-up vis variables
    let svg = d3.select("#search-count");
    svg.selectAll("g").remove(); // clear current svg
    let margin = {top: 20, right: 10, bottom: 80, left: 40},
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom,
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // create the bands to set domains
    // we need two x-axis bands: one for ticks, the other for the bars within ticks
    var x0 = d3.scaleBand().rangeRound([0, width]).paddingInner(0.1);
    var x1 = d3.scaleBand().padding(0.05);
    var y = d3.scaleLinear().rangeRound([height, 0]);
    var z = d3.scaleOrdinal()
        .range(["rgb(0, 100, 150)", "rgba(0, 150, 100, 0.5)"]);

    x0.domain(chart_data.map(function(d) { return d.name; }));
    x1.domain(keys).rangeRound([0, x0.bandwidth()]);
    y.domain([0, d3.max(chart_data, function(d) { 
        return d3.max(keys, function(key) { return d[key]; }); 
        })]).nice();
    // draw our bars
    g.append("g")
        .selectAll("g")
        .data(chart_data)
        .enter().append("g")
            .attr("transform", function(d) { return "translate(" + x0(d.name) + ",0)"; })
        .selectAll("rect")
        .data(function(d) {
            return keys.map(function(key) {
                return { key: key, value: d[key], name:d.name };
            });
        })
        .enter().append("rect")
            .attr("x", function(d) { return x1(d.key); })
            .attr("y", function(d) { return y(d.value); })
            .attr("height", function(d) { return height - y(d.value); })
            .attr("width", x1.bandwidth())
            .attr("class", "bar")
            .attr("fill", function(d) { return z(d.key);})
        .append("title")
            .text(function(d) { return d.name + ": " + d.value; });
    
    // list all the data points that deserve a label
    // i.e. frequency > mean frequency
    // this is to avoid clutter because we have 181 x-axis ticks
    let label_x = {};
    for(let i = 0; i < chart_data.length; i++) {
        if(chart_data[i].freq > y_mean) {
            label_x[chart_data[i].name] = true;
        } else {
            if(typeof(chart_data[i].new) != "undefined") {
                if(chart_data[i].new > y_mean) {
                    label_x[chart_data[i].name] = true;                    
                }
            }
        }
    }
    // label the x axis
    g.append("g")
        .attr("class", "axis")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x0))
        .selectAll("text")
            .style("text-anchor", "start")
            .style("font-size", "8px")
            .style("visibility", function(d) {
                if(typeof(label_x[d]) == "undefined") {
                    return "hidden";
                } else {
                    return "visible";
                }
            })
            .attr("transform", "translate(5,3)rotate(35)")
        .append("title")
            .text(function(d) { return d; });
    // label the y axis
    g.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(y).ticks(10).tickFormat(d3.format(".0s")))
        .append("text")
        .attr("x", 2)
        .attr("y", y(y.ticks().pop()) + 0.5)
        .attr("dy", "0.32em")
        .attr("fill", "#000")
        .attr("font-weight", "bold")
        .attr("text-anchor","end");
    // draw a legend
    let legend = g.append("g")
        .attr("font-family", "sans-serif")
        .attr("font-size", 10)
        .attr("text-anchor", "start")
        .selectAll("g")
        .data(keys.slice().reverse())
        .enter().append("g")
        .attr("transform", function(d, i) { 
            return "translate(0," + i * 20 + ")"; 
        });
    // squares to depict color
    legend.append("rect")
        .attr("x", 5)
        .attr("width", 15)
        .attr("height", 15)
        .attr("fill", z);
    // and now label
    legend.append("text")
        .attr("x", 25)
        .attr("y", 7.5)
        .attr("dy", "0.32em")
        .text(function(d) { 
            if(d == "freq") return "Current Results";
            else return "New Results";
            return d; 
        });
}


// unstack the barchart that displays journal counts
function resetJournalCount() {
    if(typeof(chart_data) == "undefined") return;
    for(let i = 0; i < chart_data.length; i++) {
        chart_data[i].freq = chart_data[i].new;
        delete chart_data[i].new;
    }
    drawJournalCount(chart_data, false);
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
            .sum(function(d) { return 10; })
            .sort(function(a, b) { return b.height - a.height});
    
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
            .attr("transform", function(d) { return "translate(" + [d.x0, d.y0] + ")"; })
            .attr("tier-index", function(d) { return d.data.parent; })
            .attr("id", function(d) { return d.data.heading_id; })
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
                    return d.data.name.toUpperCase();
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

            node.append("text")
                .attr("text-anchor", "end")
                .text(function(d) {
                    console.log(d);
                    return " (" + d.data.length + ")"; 
                })
                .attr("x", function(d) { return d.x1-d.x0-(5*(d.data.length.length-1))-16; })
                .attr("y", function(d) { return d.y1-d.y0-6; })
                .style("fill", function(d) {
                    var new_d = d;
                    if(d.data.cat == 0) {
                        new_d.data.tier = 1;
                    } else {
                        new_d.data.tier -= 2;                        
                    }
                    return getColor(new_d);
                });

            // add a title for when a node is hovered
            node.append("title")
                .text(function(d) {                     
                    return d.data.name.toUpperCase();
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
            width = text.attr("box-width")-padding,
            tspan = text.text(null).append("tspan").attr("x", 0).attr("dy", lineHeight + "em");
        while (word = words.pop()) {
            line.push(word);
            tspan.text(line.join(" "));
            if (tspan.node().getComputedTextLength() > width && line.length > 1) {
                line.pop();
                tspan.text(line.join(" "));
                line = [word];
                tspan = text.append("tspan").attr("x", 5).attr("dy", lineHeight + "em").text(word);
            }
        }
    });
}

// the drawing of vis can be request heavy, so let's queue them up
// and draw updates synchronously async to let the page load
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
        + container_path + "'><button class='close' style='z-index:999;' onclick='deleteTerm(event);'>\
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

// draw the keyword in the search query box
function drawKeyword(keyword, heading_id, draw_count = false) {
    let id = heading_id;
    if(typeof(heading_id) == "undefined") {
        id = "";
    }
    var $box = $("<div class='term-container text-center custom-keyword' id='keyword-"
    + (new Date()).getTime() + "' onclick='openExploreVis(\"" 
    + id + "\")'><button class='close' style='z-index:999;' onclick='deleteTerm(this);'>\
    <span>&times;</span></button><input type='hidden' class='custom-keyword-weight' value='1'/>\
    <div class='custom-keyword-heading' heading-id='" + id + "'>" + keyword + "</div></div>");
    $("#add-term").before($box);
    resortable();
    // we want the journal counts to show potential changes
    // whenever the search query changes
    if(draw_count) {
        updateJournalCount(true);
    }
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

    // if($("#modal-heading-id").val() == d.data.heading_id) {
    //     return default_color(0);
    // }

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


// get journal distribution of erudit
function getJournalCount( data, merge_chart=true ) {
    var post_data = JSON.stringify({"keyword_list": []});
    if(typeof(data) != "undefined" && data != null) {
        post_data = JSON.stringify(data);
    }
    // created a timeout for this hook so that the vis is not
    // regenerated every time when adding/removing multiple search items
    if(journal_timeout) {
        clearTimeout(journal_timeout);
    }
    journal_timeout = setTimeout(function() {
        $.ajax({
            url: "erudit/journal_count"
            , contentType: "application/json"
            , data: post_data
            , dataType: "json"
            , type: "POST"
            , success: function(data) {
                drawJournalCount(data, merge_chart);
            }
        });
    }, 500);
}

// get the current search terms in a json format
function getSearchTerms() {
    let keyword_list = [];
    $("#search-term-box .term-container").each(function(i) {
        if($(this).hasClass("custom-keyword")) {
            keyword_list.push( {
                "heading_id": $(".custom-keyword-heading", $(this)).attr("heading-id"),
                "keyword": $(".custom-keyword-heading", $(this)).html(),
                "weight": $(".custom-keyword-weight", $(this)).val()-1,
                "order": i+1
            });
        }
    });
    return keyword_list;
}