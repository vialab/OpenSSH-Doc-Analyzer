/******************************************************************************
 * vis.js
 * The meat of the OHT visualization tool to look for new search terms
 * * Last updated: 07/01/2018
 *****************************************************************************/

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

// hierarchical data conversion function from csv
let stratify = d3.stratify()
    .id(function(d) { return d.heading_id; })
    .parentId(function(d) { return d.parent; });
let duration = 750;

// queue of visualizations to request
let hook_busy = false;
let vis_queue = [];
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
// d3 does not support jquery.click() events for some reason
jQuery.fn.d3click = function () {
    this.each(function (i, e) {
        var evt = new MouseEvent("click");
        e.dispatchEvent(evt);
    });
};

$.fn.textWidth = function(){
        let html_org = $(this).html();
        let html_calc = '<span>' + html_org + '</span>';
        $(this).html(html_calc);
        let width = $(this).find('span:first').width();
        $(this).html(html_org);
        return width;
    };

// args:
// svg_path - path to the parent where SVG is to exist
// svg_id   - id of the svg
// path     - base URL for data requet
// id       - tier-index
function createNewVis(svg_path, svg_id, path, id, width, height, cb_keyword) {
    selected_heading = id;
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
    svg.attr("id", svg_id);
    svg.attr("tier-index", id);
    let pack = d3.tree().size([height, width]);
    if(hook_busy) {
        // queue this request and wait for others to finish first
        let temp = {
            "svg":svg
            , "pack":pack
            , "path":path
            , "id":id
            , "cb_keyword":cb_keyword
        }
        vis_queue.push(temp);
    } else {
        // draw the circle pack
        update(svg, pack, path, id, cb_keyword);
    }
}

// update a vis with new tier index
function update(svg, pack, path, id, cb_keyword) {
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
            if(parseInt(d.data.set_size) > max_node_size) {
                max_node_size = d.data.set_size;
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
        let circle_size = max_circle_size;
        nodeEnter.append('circle')
        .attr('class', 'node')
        .attr('r', 1e-6)
        .style("fill", function(d) {
            if(d.depth == 2) {
                let height = $("#search-dialog-main").height();
                circle_size = (height / d.parent.children.length)/2;
                if(circle_size < min_circle_size) circle_size = min_circle_size;
            }
            if(circle_size > max_circle_size) circle_size = max_circle_size;
            return d._children ? "lightsteelblue" : "#fff";
        });

        // // Add labels for the nodes
        nodeEnter.append('text')
            .attr("dy", ".35em")
            .attr("dx", function(d) {
                return -3 + (d.data.set_size.toString().length * -2) + 1;
            })
            .attr("fill", function(d) {
                return d.data.length > 0 ? "rgb(0,0,0)" : "rgb(255,255,255)";
            })
            .text(function(d) {
                return d.data.set_size;
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
                let r = circle_size*(d.data.set_size/max_node_size);
                if(r < min_circle_size) r = min_circle_size;
                return r;
            })
            .style("fill", function(d) {
                let cat_color = "rgb(255,255,255)";
                switch(d.data.cat) {
                  case "1":
                    cat_color = "#ddece2";
                    break;
                  case "2":
                    cat_color = "#e2eef7";
                    break;
                  case "3":
                    cat_color = "#f5e5e0";
                    break;
                }
                return d.data.length > 0 ? cat_color : "rgb(155,155,155)";
            })
            .attr("data-cat", function(d) {
                let cat = "";
                if(d.data.length > 0) {
                  if(d.data.cat == "1") cat = "earth";
                  if(d.data.cat == "2") cat = "mind";
                  if(d.data.cat == "3") cat = "society";
                }
                return cat;
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
                    + "</span><span class='super-script'>" + d.data.length
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

        selected_heading = id;

        $("foreignObject", function() {
            $(this).width($(".hl-label", this).width());
            $(this).height($(".hl-label", this).height());
        });
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
            if((d.data.length == "0" && d.data.heading_id != "root")
                || d.data.heading_id == selected_heading) {
                // don't update if there's nothing to load
                // or if we already have this heading loaded
                return;
            }
            // otherwise we double clicked another tier
            let $container = $(this).closest("svg");
            let svg_id = $container.attr("id");
            let width = $container.attr("width");
            let height = $container.attr("height");
            let pack = d3.tree().size([height, width]);
            last_heading = "";
            selected_heading = "";
            $(".hl-label").removeClass("hl-label");
            $(".selected").removeClass("selected");
            // update the circle pack to show new tier
            update(d3.select("svg#" + svg_id), pack, "/oht/", d.id, cb_keyword);
        }
    }
}

// the drawing of vis can be request heavy, so let's queue them up
// and draw updates synchronously async to let the page load
function processNextUpdateRequest() {
    if(vis_queue.length > 0) {
        let temp = vis_queue.pop();
        update(temp.svg, temp.pack, temp.path, temp.id, temp.cb_keyword);
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

// populate pos for this heading onto vis
function populatePOS(data, selected_pos) {
    $(".part-of-speech #pos-words").html("");
    for(let i = 0; i < data.length; i ++) {
        let html = "<div class='pos-container";
        if(selected_pos == data[i].pos) {
            html += " active";
        }
        if(parseInt(data[i].size) == 0) {
            html += " empty'";
        } else {
            html += "' onclick='getSynset(this, \"" + data[i].id + "\");'"
        }
        html += ">";
        html += data[i].pos + ". " + data[i].name + " (" + data[i].size + ")";
        html += "</div>";
        $(".part-of-speech #pos-words").append(html);
    }
}

// populate bag of words for this heading onto vis
function populateBOW(data, quick_search, tier_index) {
    $(".word-box #heading-words").html("");
    $(".search-side #heading-words").height($(window).height()
        - $(".search-side.part-of-speech").height() - 330);
    $(".search-side.part-of-speech #pos-words").css("max-height", $(window).height() * 0.3);
    // add new keywords from synset
    for(let i = 0; i < data.length; i ++) {
        let html = "<div class='bow-word text-center";
        if(data[i]["enable"]) {
            if(quick_search) {
                html += "' onclick='window.location.href=\"/analyzer?quicksearch=" + data[i]["id"] + "\"');'";
            } else {
                html += "' onclick='drawKeyword(\"" + data[i]["name"] + "\", \"" + data[i]["heading_id"] + "\",\"" + data[i]["tier_index"] + "\", true, \""+data[i]["enable"]+"\");'";
            }
        } else {
            html += " no-click'";
        }
        html += ">" + data[i]["name"] + "</div>";
        $(".word-box #heading-words").append(html);
    }
}

// what happens when a keyword is clicked in search dialog vis
function keywordClicked(d) {
    let new_tier_index = d.data.parent;
    let $target = $("#"+target, "#"+target_parent);
    let $container = $target.parent().parent();
    let weight = ($("#weight-slider").val()-1) * 0.25;
    let vis_size = min_size + (add_size * weight);

    // draw the mini-vis to the dom element
    createNewVis("#search-term-box #"+target_parent, target, "/oht/"
        , new_tier_index, vis_size, vis_size);

    $target.attr("tier-index", new_tier_index);

    // highlight what was just changed for visual feedback
    animate("select", $("#"+target_parent).parent());
}

// select the color of a vis item based on their category
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

function flattenQueryData(data) {
    let zip_data = [];
    for(let i in data[0].values) {
        for(let j in data) {
            zip_data.push(data[j].values[i].y);
        }
    }
    return zip_data;
}

function drawTier($target, tier) {
  let tiers = tier.split(".");
  let root = $target;
  let classes = "ring";
  switch(tiers[0]) {
    case "1":
      classes += " earth";
      break;
    case "2":
      classes += " mind";
      break;
    case "3":
      classes += " society";
      break;
  }
  for(let i=0; i<7; i++) {
    if((tiers[i] == "NA" && i>0) || tiers[i] === undefined) break;
    let child = $("<div class='" + classes + "'/>");
    let dim = 120-(i*15);
    child.css({
    	"width": dim+"px",
      "height": dim+"px"
    })
  	root.append(child);
    root = child;
  }
}
