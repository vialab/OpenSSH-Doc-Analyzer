/******************************************************************************
 * widget.js
 * The meat of the Query Results widget on the /analyzer page
 * * Last updated: 07/01/2018
 *****************************************************************************/
let journal_size_ratio = 0.15;
let journal_count_margin = 15;
let journal_count_minimized = true;
let journal_timeout;

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
            , "opacity": 0.5
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

// update the journal count vis
function updateJournalCount(merge=false) {
    let keyword_list = getSearchTerms();
    if(keyword_list.length > 0) {
        getJournalCount({"keyword_list":keyword_list}, merge);
    }
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

// maximize the journal count vis modal
function maximizeJournalCount(e) {
    let height = $(window).height() - (journal_count_margin*2)
    - ($(".navbar-collapse").height() + $("#search-term-box").height());
    let width = $(window).width()-(journal_count_margin*2);
    $(this).css({"width": width
        , "height": height
        , "right":journal_count_margin
        , "opacity": 1
    });
    redrawJournalCount(false);
    $("button.close", this).show();
    e.stopPropagation();
}

// redisplay journal count without changing data
function redrawJournalCount(minimize, cancel_bubble=false, use_old=true) {
    drawJournalCount(chart_data, false, minimize, use_old);
    if(cancel_bubble) window.event.cancelBubble = true;
}
