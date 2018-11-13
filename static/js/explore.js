// maintain focus target
let focus_id = "";

// set the dimensions and margins of the vis
let margin = {top: 20, right: 90, bottom: 30, left: 90};
let padding = 20;
let min_size = 100;
let add_size = 50;
let format = d3.format(",d");
let oneclick = false;
let click_to;
let chart_data;
let old_chart_data;
let max_node_size = 0;
let max_circle_size = 50;
let min_circle_size = 10;
let journal_size_ratio = 0.15;
let journal_count_margin = 15;
let journal_count_minimized = true;
// hierarchical data conversion function from csv
let stratify = d3.stratify()
    .id(function(d) { return d.heading_id; })
    .parentId(function(d) { return d.parent; });
let duration = 750;

// queue of visualizations to request
let hook_busy = false;
let vis_queue = [];
let journal_timeout;
// color scale for depth
let world_color = d3.scaleLinear()
    .domain([-2, 6])
    .range(["hsl(132,80%,80%)", "hsl(202,30%,40%)"])
    .interpolate(d3.interpolateHcl);
let mind_color = d3.scaleLinear()
    .domain([-2, 6])
    .range(["hsl(182,80%,80%)", "hsl(252,30%,40%)"])
    .interpolate(d3.interpolateHcl);
let society_color = d3.scaleLinear()
    .domain([-2, 6])
    .range(["hsl(212,80%,80%)", "hsl(302,30%,40%)"])
    .interpolate(d3.interpolateHcl);
let default_color = d3.scaleLinear()
    .domain([0, 1])
    .range(["#fff", "#000"])
    .interpolate(d3.interpolateHcl);

$.fn.textWidth = function(){
        let html_org = $(this).html();
        let html_calc = '<span>' + html_org + '</span>';
        $(this).html(html_calc);
        let width = $(this).find('span:first').width();
        $(this).html(html_org);
        return width;
    };
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
            let click_to = setTimeout(function() {
                if(oneclick) {
                    cb_keyword(d);
                }
                oneclick = false;
            }, 250);
            // d3.select(this).style("stroke", "rgb(220,100,100)");
            let self = this;
            d3.selectAll(".select-path").remove();
            d3.select(self).append("path")
                .attr("class", "link")
                .attr("class", "select-path")
                .attr('d', function(d){
                    let p = d3.select(this.parentNode);
                    let t = p.attr("transform").split(",");
                    t[0] = d3.select("svg")._groups[0][0].clientWidth - parseFloat(t[0].replace("translate(", ""));
                    t[1] = -parseFloat(t[1].replace(")", ""))+20;
                    let r = parseInt(p.select("circle").attr("r"));
                    r += $(p.select("foreignObject body div span.node-label")._groups[0][0]).width()+30;
                    let o = {x:-5,y:r};
                    let o2 = {x:t[1],y:t[0]};
                    return diagonal(o2, o);
                });
            
            d3.selectAll("foreignObject body")
                .attr("class", "");
            
            d3.selectAll("circle.node")
                .attr("class", "node");

            d3.select(self)
                .select("foreignObject body")
                .attr("class", "hl-label")
                .attr("style", function(d) {
                    let p = d3.select(this.parentNode);
                    let r = $(p.select("foreignObject body div span.node-label")._groups[0][0]).width()+25;
                    return "width:" + r + "px;";
                });

            d3.select(self)
                .select("circle.node")
                .attr("class", "node selected")
        } else {
            oneclick = false;
            clearTimeout(click_to);
            if(d.data.length == "0" && d.data.heading_id != "root") {
                return;
            }
            // otherwise we double clicked another tier
            let $container = $(this).closest("svg");
            let svg_id = $container.attr("id");
            let width = $container.attr("width");
            let height = $container.attr("height");
            // let pack = d3.pack().size([width, height]).padding(padding);  
            // let pack = d3.treemap()
            //     .size([width, height])
            //     .paddingOuter(padding)
            //     .tile(d3.treemapBinary);
            let pack = d3.tree().size([height, width]);
            last_heading = "";
            selected_heading = "";
            $(".hl-label").removeClass("hl-label");
            $(".selected").removeClass("selected");
            // update the circle pack to show new tier
            update(d3.select("svg#" + svg_id), pack, "/oht/", d.id, true
                , true, true, d.data.heading_id, cb_keyword);
        }
    }
}

function maximizeJournalCount(e) {
    let height = $(window).height() - (journal_count_margin*2)
    - ($(".navbar-collapse").height() + $("#search-term-box").height());
    let width = $(window).width()-(journal_count_margin*2);
    $(this).css({"width": width, "height": height, "right":journal_count_margin});
    redrawJournalCount(false);
    $("button.close", this).show();
    e.stopPropagation();
}

// redisplay journal count without changing data
function redrawJournalCount(minimize, cancel_bubble=false, use_old=true) {
    drawJournalCount(chart_data, false, minimize, use_old);
    if(cancel_bubble) window.event.cancelBubble = true;
}

// create a barchart to display distribution
function drawJournalCount(data, merge, minimize=true, use_old=false) {
    journal_count_minimized = minimize;
    $("#journal-count").unbind();
    let keys = ["freq"];
    let y_mean = 0;
    let has_new = false;
    // append new query data to current if we have new search query
    // also calculate the mean for label filtering
    if(merge && typeof(chart_data) != "undefined") {
        let n = 0, sum = 0;
        for(let i = 0; i < chart_data.length; i++) {
            chart_data[i].new = data[i].freq;
            chart_data[i].total = data[i].freq + chart_data[i].freq;
            sum += chart_data[i].total;
            n += 2;
        }
        y_mean = sum / n;
        keys.push("new");
        has_new = true;
    } else if(!use_old) {
        // not appending, but we still want to calculate the mean
        chart_data = data;
        let n = 0, sum = 0;
        for(let i = 0; i < chart_data.length; i++) {
            chart_data[i].total = chart_data[i].freq;
            sum += chart_data[i].total;
            n += 1;
        }
        y_mean = sum / n;
    }
    let new_chart_data = [{
        "id":"old",
        "values":[]
    }];
    let new_query = {
        "id":"new",
        "values":[]
    };
    let count = 0;
    let journal_names = []
    for(let i = 0; i < chart_data.length; i++) {
        if(chart_data[i].total > 0) {
            journal_names.push(chart_data[i].name);
            chart_data[i]["key"] = count;
            temp = {
                "name": chart_data[i].name,
                "x": count,
                "y": chart_data[i].freq
            };
            new_chart_data[0].values.push(temp);
            if(has_new) {
                new_temp = {
                    "name": chart_data[i].name,
                    "x": count,
                    "y": chart_data[i].new
                };
                new_temp.y = chart_data[i].new;
                new_query.values.push(new_temp);
            }
            count++;
        } else {
            continue;
        }
    }

    if(has_new) { 
        new_chart_data.push(new_query);
    }

    if(use_old) {
        new_chart_data = old_chart_data;
    } else {
        old_chart_data = new_chart_data;
    }

    let flat_data = flattenQueryData(new_chart_data);
    
    // start-up vis letiables
    var barHeight        = 20,
        groupHeight      = barHeight * new_chart_data.length,
        gapBetweenGroups = 10,
        spaceForLabels   = 250,
        spaceForLegend   = 150;

    // Color scale
    let margin = {top: 40, right: 40, bottom: 40, left: 40};
    let height = barHeight * flat_data.length + gapBetweenGroups * new_chart_data[0].values.length,
    width = $(window).width() - margin.left - margin.right;

    if(minimize) {
        height = $(window).height()*journal_size_ratio;
        width = $(window).width()*journal_size_ratio;
        right = journal_count_margin
        if(searching && !peeking) {
            right = -width+journal_count_margin
        }
        $("#journal-count").css({
            "bottom": $("#search-term-box").height()+journal_count_margin
            , "right": right
            , "height": height
            , "width": width
        });
        barHeight = height / new_chart_data[0].values.length;
        if(barHeight > 20) barHeight = 20;
        groupHeight = barHeight * new_chart_data.length;
        gapBetweenGroups = 0;
        spaceForLabels = 0;
        spaceForLegend = 0;
        $("button.close","#journal-count").hide();
        $("#journal-count").click(maximizeJournalCount);
    }

    let svg = d3.select("#search-count")
        .attr("class", "chart")
        .attr("width", width)
        .attr("height", height);

    let color = d3.scaleOrdinal(d3.schemeCategory20);

    var x = d3.scaleLinear()
        .domain([0, d3.max(flat_data)])
        .range([0, width - spaceForLabels - spaceForLegend]);

    var y = d3.scaleLinear()
        .range([height + gapBetweenGroups, 0]);

    var yAxis = d3.axisLeft(y)
        .tickFormat('')
        .tickSize(0);

    svg.selectAll("g").remove();    

    // Create bars
    var bar = svg.selectAll("g")
        .data(flat_data)
        .enter().append("g")
        .attr("transform", function(d, i) {
            return "translate(" + spaceForLabels + "," + (i * barHeight + gapBetweenGroups * (0.5 + Math.floor(i/new_chart_data.length))) + ")";
        });

    // Create rectangles of the correct width
    bar.append("rect")
        .attr("fill", function(d,i) { return color(i % new_chart_data.length); })
        .attr("class", "bar")
        .attr("width", x)
        .attr("height", barHeight - 1);

    // Draw labels
    if(!minimize) {
        // Add text label in bar
        bar.append("text")
            .attr("x", function(d) { return x(d) - 3; })
            .attr("y", barHeight / 2)
            .attr("fill", "red")
            .attr("dy", ".35em")
            .text(function(d) { return d; });
        bar.append("text")
        .attr("class", "label")
        .attr("x", function(d) { return - 10; })
        .attr("y", groupHeight / 2)
        .attr("dy", ".35em")
        .text(function(d,i) {
            if (i % new_chart_data.length === 0)
                return new_chart_data[0].values[Math.floor(i/new_chart_data.length)].name;
            else
                return ""
        });
    }

    svg.append("g")
        .attr("class", "y axis")
        .attr("transform", "translate(" + spaceForLabels + ", " + -gapBetweenGroups/2 + ")")
        .call(yAxis);

    $("#journal-count").show();
    
    if(minimize) return;

    // Draw legend
    var legendRectSize = 18,
        legendSpacing  = 4;

    var legend = svg.selectAll('.legend')
        .data(new_chart_data)
        .enter()
        .append('g')
        .attr('transform', function (d, i) {
            var height = legendRectSize + legendSpacing;
            var offset = -gapBetweenGroups/2;
            var horz = spaceForLabels + width + 40 - legendRectSize - spaceForLabels - spaceForLegend;
            var vert = i * height - offset;
            return 'translate(' + horz + ',' + vert + ')';
        });

    legend.append('rect')
        .attr('width', legendRectSize)
        .attr('height', legendRectSize)
        .style('fill', function (d, i) { return color(i); })
        .style('stroke', function (d, i) { return color(i); });

    legend.append('text')
        .attr('class', 'legend')
        .attr('x', legendRectSize + legendSpacing)
        .attr('y', legendRectSize - legendSpacing)
        .text(function (d) { return d.id; });
}

function flattenQueryData(data) {
    let zip_data = [];
    for(let i in data[0].values) {
        for(let j in data) {
            zip_data.push(data[j].values[i].y);
        }   
    }
    return zip_data;
}

function journalToolTip(div, d) {
    div.transition()		
        .duration(200)		
        .style("opacity", 0.9);
    div.html(d.name + "<br/>"  + d.y)	
        .style("left", (d3.event.pageX) + "px")		
        .style("top", (d3.event.pageY - 28) + "px");	
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
    let svg = null;
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
    
    // let pack = d3.pack().size([width-5, height-5]).padding(padding);
    // let pack = d3.treemap()
    // .size([width, height])
    // .paddingOuter(padding)
    // .tile(d3.treemapBinary);
    let pack = d3.tree().size([height, width]);
    
    if(hook_busy) {
        // queue this request and wait for others to finish first
        let temp = {
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

    let url_path = path + id;
    hook_busy = true;
    max_node_size = 0;
    // get the new tier nodes from the server
    d3.csv(url_path, function(error, data) {
        if (error) throw error;
        
        // convert the flat data into a hierarchy 
        let root = stratify(data)
            .sum(function(d) { return 10; })
            .sort(function(a, b) { return b.height - a.height});
        // let root = d3.hierarchy(data, function(d) { return d.children; });
        root.x0 = svg._groups[0][0].clientHeight / 2;
        root.y0 = 0;

        // assign the name to each node
        root.each(function(d) {
            d.name = d.id;
        });
        // root.children.forEach(collapse);
                // Collapse the node and all it's children
        function collapse(d) {
            if(d.children) {
                d._children = d.children
                d._children.forEach(collapse)
                d.children = null
            }
        }
        d3.select(".select-path").remove();
        // convert hierarchy data to circle pack data
        let treeData = pack(root);
        // Compute the new tree layout.
        let nodes = treeData.descendants(),
        links = treeData.descendants().slice(1);

        // Normalize for fixed-depth.
        nodes.forEach(function(d){ 
            if(d.parent != null) {
                d.y = d.depth * 250;
            } else {
                d.y = 80;
            }
            if(parseInt(d.data.child_size) > max_node_size) {
                max_node_size = d.data.child_size;
            }
        });

        // ****************** Nodes section ***************************

        // Update the nodes...
        let node = svg.selectAll('g.node')
            .data(nodes, function(d) {return d.id || (d.id = ++i); });

        // Enter any new modes at the parent's previous position.
        let nodeEnter = node.enter().append('g')
            .attr('class', function(d) { return 'node ' + d.id; })
            .attr("transform", function(d) {
                if(d.parent!=null) {
                    return "translate(" + d.parent.y + "," + d.parent.x + ")";
                } else {
                    return "translate(" + 0 + "," + root.x0 + ")";
                }
            })
            .on('click', clicked(cb_keyword));

        // Add Circle for the nodes
        nodeEnter.append('circle')
        .attr('class', 'node')
        .attr('r', 1e-6)
        .style("fill", function(d) {
            return d._children ? "lightsteelblue" : "#fff";
        });

        // // Add labels for the nodes
        nodeEnter.append('text')
            .attr("dy", ".35em")
            .attr("dx", function(d) {
                return -3 + (d.data.child_size.toString().length * -2) + 1;
            })
            .attr("fill", function(d) {
                return d.data.child_size > 0 ? "rgb(0,0,0)" : "rgb(255,255,255)";
            })
            .text(function(d) { 
                return d.data.child_size; 
            });


        // UPDATE
        let nodeUpdate = nodeEnter.merge(node);

        // Transition to the proper position for the node
        nodeUpdate.transition()
            .duration(duration)
            .attr("transform", function(d) { 
                return "translate(" + d.y + "," + d.x + ")";
            })
            .on("end", function(d) {
                if(selected_heading != last_heading) {
                    $("g.node."+selected_heading).d3click();
                }
            });

        // Update the node attributes and style
        nodeUpdate.select("circle.node")
            .attr("r", function(d) {
                let circle_size = max_circle_size;
                if(d.depth == 2) {
                    let height = $("#search-dialog-main").height();
                    circle_size = (height / d.parent.children.length)-(journal_count_margin);
                    if(circle_size < min_circle_size) circle_size = min_circle_size;
                }
                if(circle_size > max_circle_size) circle_size = max_circle_size;
                let r = circle_size*(d.data.child_size/max_node_size)+8;
                return r;
            })
            .style("fill", function(d) {
                return d.data.child_size > 0 ? "rgb(255,255,255)" : "rgb(155,155,155)";
            })
            .attr("cursor", "pointer");

        nodeEnter.append('foreignObject')
            .attr("x", function(d) {
                let r = parseInt(d3.select(this.parentNode).select("circle").attr("r"))+5;
                return r;
            })
            .attr("y", -10)
            .append('xhtml:body')
            .html(function(d) { 
                return "<div><span class='node-label'>" + d.data.name 
                    + "</span><span class='super-script'>" + d.data.set_size 
                    + "</span>" + "</div>"; 
            });

        // Remove any exiting nodes
        let nodeExit = node.exit().transition()
            .duration(duration)
            .attr("transform", function(d) {
                if(d.parent != null) {
                    return "translate(" + d.parent.y + "," + d.parent.x + ")";
                } else {
                    return "translate(" + 80 + "," + root.x0 + ")";
                }
            })
            .remove();

        // On exit reduce the node circles size to 0
        nodeExit.select('circle')
            .attr('r', 1e-6);

        // On exit reduce the opacity of text labels
        nodeExit.select('text')
            .style('fill-opacity', 1e-6);

        // ****************** links section ***************************

        // Update the links...
        let link = svg.selectAll('path.link')
            .data(links, function(d) { return d.id; });

        // Enter any new links at the parent's previous position.
        let linkEnter = link.enter().insert('path', "g")
            .attr("class", "link")
            .attr('d', function(d){
                if(d.parent != null) {
                    let o = {x: d.parent.x, y: d.parent.y}
                    return diagonal(o, o)    
                } else {
                    let o = {x: root.x0, y: root.y0}
                    return diagonal(o, o)    
                }
            });

        // UPDATE
        let linkUpdate = linkEnter.merge(link);

        // Transition back to the parent element position
        linkUpdate.transition()
            .duration(duration)
            .attr('d', function(d){ return diagonal(d, d.parent) });

        // Remove any exiting links
        let linkExit = link.exit().transition()
            .duration(duration)
            .attr('d', function(d) {
                if(d.parent != null) {
                    let o = {x: d.parent.x0, y: d.parent.y0}
                    return diagonal(o, o);   
                } else {
                    let o = {x: root.x0, y: root.y0}
                    return diagonal(o, o);
                }
            })
            .remove();

        // Store the old positions for transition.
        nodes.forEach(function(d){
            d.x0 = d.x;
            d.y0 = d.y;
        });

        // Toggle children on click.
        function click(d) {
            if (d.children) {
                d._children = d.children;
                d.children = null;
            } else {
                d.children = d._children;
                d._children = null;
            }
            update(d);
        }
        processNextUpdateRequest();
    });
}

// Creates a curved (diagonal) path from parent to the child nodes
function diagonal(s, d) {
    path = `M ${s.y} ${s.x}
            C ${(s.y + d.y) / 2} ${s.x},
            ${(s.y + d.y) / 2} ${d.x},
            ${d.y} ${d.x}`
    // path = "M" + s.x + "," + s.y
    // + "C" + s.x + "," + (s.y + d.y) / 2
    // + " " + d.x + "," +  (s.y + d.y) / 2
    // + " " + d.x + "," + d.y;
    return path;
}

// Used to calculate and reposition text in the visualization
function wrap(text) {
    text.each(function() {
        let text = d3.select(this),
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
        let temp = vis_queue.pop();
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
    let container_path = "term-" + tier_id;
    container_path += "-" + $("[id^=" + container_path + "]").length.toString();
    let svg_path = "term-vis-" + tier_id;
    svg_path += "-" + $("[id^=" + svg_path + "]").length.toString();
    
    // search term html
    let $box = $("<div class='term-container text-center' id='"
        + container_path + "'><button class='close' style='z-index:999;' onclick='deleteTerm(event);'>\
        <span>&times;</span></button><input type='hidden' class='term-heading-id' value='" 
        + heading_id +"'/><input type='hidden' class='term-heading-weight' value='1'/>\
        <div class='term-heading'>" + heading_text + "</div><div class='term-vis' id='" 
        + svg_path + "'></div></div>");
    
    // prepend before add term button
    $("#add-term").before($box);
    let vis_size = min_size + (add_size * weight);
    
    svg_path = "#" + svg_path;
    // color scale for depth
    let color = d3.scaleLinear()
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
function drawKeyword(keyword, heading_id, draw_count = false, term_id = "") {
    let already_used = false;
    $("#search-term-box .term-container").each(function(i) {
        let used_keyword = $(".custom-keyword-heading", $(this)).html()
        if(keyword == used_keyword) {
            already_used = true;
            $.each($(".star", $(this)), function() {
                toggleStar(this);
            });
        }
    });
    if(already_used) return;

    let id = heading_id;
    if(typeof(heading_id) == "undefined") {
        id = "";
    }
    let $box = $("<div class='term-container text-center custom-keyword new-search-term' id='keyword-"
    + (new Date()).getTime() + "' data-termid='" + term_id + "' onclick='openExploreVis(\"" 
    + id + "\")'><button class='close' style='z-index:999;'\
     onclick='deleteTerm(this);'><span>&times;</span></button><input type='hidden' \
     class='custom-keyword-weight' value='1'/><div class='custom-keyword-heading' heading-id='" 
     + id + "'>" + keyword + "</div><span onclick='toggleStar(this);' class='star'>&#9698;</span></div>");
    $("#add-term").before($box);
    resortable();
    // we want the journal counts to show potential changes
    // whenever the search query changes
    if(draw_count) {
        updateJournalCount(true);
    }
}

// sets an html element to toggle a force inclusion for the search query 
function toggleStar(elem, cancel_bubble=true, draw_count=true) {
    if($(elem).hasClass("active")) {
        $(elem).removeClass("active");
        $(elem).removeClass("new");
        $(elem).addClass("old");
    } else {
        $(elem).addClass("active");
        $(elem).addClass("new");
    }
    if(draw_count) updateJournalCount(true);
    if(cancel_bubble) window.event.cancelBubble = true;
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
    let post_data = JSON.stringify({"keyword_list": []});
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
                drawJournalCount(data, merge_chart, journal_count_minimized);
            }
        });
    }, 500);
}

// get the current search terms in a json format
function getSearchTerms(only_words=false) {
    let keyword_list = [];
    $("#search-term-box .term-container").each(function(i) {
        if(only_words) {
            keyword_list.push($(".custom-keyword-heading", $(this)).html());
            return;
        }
        if($(this).hasClass("custom-keyword")) {
            keyword_list.push( {
                "heading_id": $(".custom-keyword-heading", $(this)).attr("heading-id"),
                "keyword": $(".custom-keyword-heading", $(this)).html(),
                "term_id": $(this).data("termid"),
                "weight": $(".custom-keyword-weight", $(this)).val()-1,
                "order": i+1,
                "must_include": $(".star", $(this)).hasClass("active")
            });
        }
    });
    return keyword_list;
}