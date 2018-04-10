var searching = true, peeking = false, keyword_searching = true; // toggle modes
var target = ""; // retain which element we are editting
var target_parent = ""; // element parent
var target_index = ""; // element tier index
var typed_interval; // interval that listens for last keypress
var vis_width = $("#search-dialog-main").width();
var selected_heading = "";

// whenever a vis is clicked, open up our search dialog
$(document).on("click", ".term-vis svg", function() {
    var $parent = $(this).parent().parent();
    // deselect all other svgs
    $(".term-container").removeClass("selected");
    // select the one we just clicked
    $parent.addClass("selected");
    // insert heading title
    $("#search-dialog-title").html($(".term-heading", $parent).html());
    
    // toggle search dialog
    if(!searching) {
        toggleSearchDialog();
    }
    
    target = $(this).attr("id");
    target_parent = $(this).parent().attr("id");
    target_index = $(this).attr("tier-index");
    // draw vis of current tier in search dialog
    var vis_height = $(window).height()-$("#search-term-container").height();
    var heading_id = $(".term-heading-id", $parent).val();

    createNewVis("#search-dialog", "search-dialog-vis", "/oht/"
        , target_index, vis_width, vis_height, 1
        , true, true, true, heading_id, headingClicked);

    // set up the weight slider bar to match selection
    var weight = $(".term-heading-weight", $parent).val();
    setWeightValue(weight);
    $("#search-dialog .slider").css("bottom"
        , $("#search-term-container").height() + 15);
});

// avail previous document results during search
$("#search-result-container").on("click", function() {
    if(peeking) {
        toggleSearchDialog();
    } else {
        togglePeek();    
    }
});

$("#search-dialog").on("click", function() {
    if(peeking) togglePeek();
});

// add a new term
$("#add-term").on("click", function() {
    // draw vis of current tier in search dialog
    var vis_height = $(window).height()-$("#search-term-container").height()-120;
    d3.select("#search-dialog-vis").remove();
    d3.select("#search-dialog-vis-parent").remove();
    d3.select("#search-dialog-vis-child").remove();
    createNewVis("#search-dialog-main", "search-dialog-vis-parent", "/oht/"
        , home_tier, vis_width, vis_height, 1
        , true, true, true, null, headingClicked
    );
    // getOhtDirectory();
    // set up the weight slider bar to match selection
    // setWeightValue(1);
    // $("#search-dialog .slider").css("bottom"
    //     , $("#search-term-container").height() + 15);
    
    searching = false;
    toggleSearchDialog();

    // draw the search term to dom
    // drawSearchTerm("1.NA.NA.NA.NA.NA.NA.1", 181456, "The world", 0);
    // open up search dialog to new term
    // var idx = $(".term-container").length-1;
    // if(idx < 0) idx = 0;
    // $($(".term-container svg")[idx]).click();
});

// if we resize the screen, close the search dialog and adjust elements
$(window).on("resize", function() {
    searching = true;
    keyword_searching = true;
    toggleSearchDialog();
    toggleKeywordDialog();
});

$("#search-keyword, #search-keyword-home").on("input click", function() {
    var keyword = $(this).val();
    $(".no-keyword").hide();    
    if(!keyword_searching) {
        if(keyword != "") {
            toggleKeywordDialog();
        } else {
            return;
        }
    } else {
        if(keyword == "") {
            toggleKeywordDialog();
            return;
        }
    }
    setKeyword(keyword);    
    // wait one second until after the person is done typing
    // before running the request
    $(".load-keyword").show();
    if(typed_interval) {
        $("#search-keyword-container .keyword-container").remove();
        clearInterval(typed_interval);
    }

    var cb_keyword = function() {
        var heading_text = $(".keyword-heading", this).html();
        var heading_id = $(this).attr("heading-id");
        var tier_index = $(this).attr("tier-index");
        // drawSearchTerm(tier_index, heading_id, heading_text, 0);
        let d = {
            "data": {
                "parent":"",
                "heading_id":heading_id,
                "name": heading_text
            }
        };
        headingClicked(d);
    };
    
    // if($(this).attr("id") == "search-keyword-home") {
    //     cb_keyword = function() {
    //         window.location.href = "/analyzer?quicksearch=" 
    //             + $(".keyword-heading", this).html() + "&headingid="
    //             + $(this).attr("heading-id") + "&tierindex="
    //             + $(this).attr("tier-index");
    //     };
    // }

    typed_interval = setTimeout(function() {
        getKeywordList(keyword, cb_keyword);
    }, 1000);
});

$(document).keyup(function(e) {
    // doesn't matter if search dialog closed
    if(!searching && !keyword_searching) {        
        return;
    }
    if (e.keyCode === 27) { // ESC key
        if(searching) {
            toggleSearchDialog();            
        }
        if(keyword_searching) {
            toggleKeywordDialog();
        }
    }
});

$(document).ready(function() {
    getJournalCount(null, "#corpus-count");
    toggleKeywordDialog();
    toggleSearchDialog();
    // instantiate drag and drop elems
    $("#search-term-box").sortable({
        items: ".term-container"
    });
    $("#modal-synset").modal({show:false});
    $("#weight-slider").slider();
    var search_id = getParameterByName("searchid");
    var quick_search = getParameterByName("quicksearch");
    var heading_id = getParameterByName("headingid");
    var tier_index = getParameterByName("tierindex");
    if(quick_search) {
        if(heading_id) {
            // drawSearchTerm(tier_index, heading_id, quick_search, 0);
            drawKeyword(quick_search, heading_id);            
        } else {
            drawKeyword(quick_search);
        }
        search();        
    } else if(search_id) {
        recoverSearch(search_id);
    }
});


function getOhtDirectory(heading_id=181456) {
    $.ajax({
        url: "oht/directory/" + heading_id
        , type: "GET"
        , contentType: "application/json"
        , success: function(data) {
            
        }
    });
}

// fetch a previously used set of search terms and search again
function recoverSearch(search_id) {
    $.ajax({
        url: "recoversearch/" + search_id
        , type: "GET"
        , contentType: "application/json"
        , success: function(content) {
            var tiers = content["tier_index"];
            home_tier = tiers.home;
            parent_tier = tiers.parent;
            child_tier = tiers.child;
            var data = content["content"];
            for(var i = 0; i < data.length; i++) {
                var weight = parseInt(data[i].weight);
                if(data[i].keyword) {
                    drawKeyword(data[i].keyword, data[i].heading_id);
                } else {
                    drawSearchTerm(data[i].tier_index
                        , data[i].heading_id, data[i].heading, weight);
                }
            }
            search(search_id);
        }
    });
}

// fetch keyword list from server and display results
function getKeywordList(keyword, cb_keyword) {
    $.ajax({
        url: "searchkeyword"
        , contentType: "application/json"
        , data: JSON.stringify({ "data":keyword })
        , dataType: "json"
        , type: "POST"
        , success: function(data) {
            showKeywordResults(data, cb_keyword);
        }
    });
}

// display a set of keywords in keyword dialog
function showKeywordResults(data, cb_keyword) {
    $(".load-keyword").hide();
    if(data.length == 0) {
        $(".no-keyword").show();    
    }
    for(i in data) {
        var clean_tier_index = data[i][4].replace(/\./g, "-");
        var svg_path = "keyword-vis-" + clean_tier_index;
        svg_path += "-" + $("[id^=" + svg_path + "]").length.toString();
        // create the container and add to dom
        var $box = $("<div class='keyword-container' id='keyword-" 
                + clean_tier_index + "' tier-index='" + data[i][4] 
                +"' heading-id='" + data[i][0] + "'>\
            <div class='keyword-heading'>" + data[i][1] + "</div>\
            <div class='keyword-vis' id='" + svg_path + "'></div>\
        </div>");
        $(".custom-keyword-container").after($box);
        // draw the mini-vis to the dom element
        createNewVis("#"+svg_path, "mini-"+clean_tier_index, "/oht/"
            , data[i][4], 100, 100, 1, false, false, false
            , data[i][0]);
    }
    $(".custom-keyword-container").off("click");
    $(".custom-keyword-container").on("click", function() {
        drawKeyword($(".keyword-heading").html());
        toggleKeywordDialog();
    });
    
    $(".custom-keyword-container.homepage").on("click", function() {
        $(this).off("click");
        window.location.href = "/analyzer?quicksearch=" + $(".keyword-heading", this).html();
    });

    $(".keyword-container").on("click", cb_keyword);
}

// set custom keyword option in keyword dialog
function setKeyword(keyword) {
    $("#search-keyword-container .keyword-heading").html(keyword);
}

// delete a search term from dom
function deleteTerm(self) {
    $(self).parent().remove();
    if(searching) {
        toggleSearchDialog();
    }
}

// open or close keyword search dialog
function toggleKeywordDialog() {
    if(keyword_searching) {
        $("#search-keyword-dialog").css("left", -$(window).width()-75);
        keyword_searching = false;
    } else {
        if(searching) {
            toggleSearchDialog();
        }
        $("#search-keyword-dialog").css("left", 0);
        keyword_searching = true;
    }
}

// open or close the search dialog
function toggleSearchDialog() {
    if(searching) { 
        // need to close
        $("#search-dialog").css("left", -$(window).width()-75);
        $("#search-result-container").css({
            "left": 0,
            "width": "100vw",
            "padding-left": "2%",
            "padding-right": "2%"
        });
        $("#search-dialog svg").css("padding-left", 0);
        $("#search-dialog-title").css("margin-left", 0);
        $("#search-dialog .slider").css("margin-left", 0);
        searching = false;
        peeking = false;
        $(".term-container").removeClass("selected");    
    } else {
        if(keyword_searching) {
            toggleKeywordDialog();
        }
        toggleCarousel();
        // need to open
        $("#search-dialog").css("left", 0);
        $("#search-result-container").css({
            "left": $("#search-dialog").width(),
            "width": "30vw",
            "padding-left": "0",
            "padding-right": "0"
        });
        searching = true;
    }
}

// instantiate slick carousel
function toggleCarousel() {
    try { $('#search-carousel').slick("unslick"); } catch(e) {}
    $('#search-carousel').slick({
        centerMode: true,
        centerPadding: '60px',
        slidesToShow: 3,
        responsive: [
        {
            breakpoint: 768,
            settings: {
            arrows: true,
            centerMode: true,
            centerPadding: '40px',
            slidesToShow: 3
            }
        },
        {
            breakpoint: 480,
            settings: {
            arrows: true,
            centerMode: true,
            centerPadding: '40px',
            slidesToShow: 1
            }
        }
        ]
    });
}

// Toggle document result view during search
function togglePeek() {
    if(searching) {
        // only relevant when search dialog is open
        var result_offset = $(window).width()-$("#search-result-container").width();
        var search_offset = ($("#search-dialog").width()+$("#search-result-container").width()) - $(window).width();
        if(peeking) {
            // need to close
            $("#search-dialog").css("left", 0);
            $("#search-dialog svg").css("padding-left", 0);
            $("#search-dialog-title").css("margin-left", 0);
            $("#search-dialog .slider").css("margin-left", 0);
            $("#search-result-container").css("left", $("#search-dialog").width());
            peeking = false;
        } else {
            // need to open
            $("#search-dialog").css("left", -(search_offset));
            $("#search-dialog svg").css("padding-left", search_offset/2);
            $("#search-dialog-title").css("margin-left", search_offset/2);
            $("#search-dialog .slider").css("margin-left", search_offset/2);
            $("#search-result-container").css("left", result_offset);
            peeking = true;
        }
    }
}

// what happens when a keyword is clicked in search dialog vis
function headingClicked(d, quick_search=false) {
    $.ajax({
        type: "GET"
        , url: "/oht/synset/" + d.data.heading_id
        , success: function(response) {
            // clear modal
            $(".word-box #heading-words", ".part-of-speech h4", "").html("");
            populateBOW(response.words, quick_search);
            populatePOS(response.pos, "n");
            // set title and go
            $(".part-of-speech h4").html(response.name);
            $("#modal-tier-index").val(response.tierindex);
            $("#modal-heading-id").val(d.data.heading_id);
            selected_heading = d.data.heading_id;
        }
    });
}


function getSynset(elem, heading_id) {
    $(".pos-container").removeClass("active");
    $(elem).addClass("active");
    $.ajax({
        type: "GET"
        , url: "/oht/synset/" + heading_id
        , success: function(response) {
            populateBOW(response.words, false);
        }
    });
}


// populate pos for this heading onto vis
function populatePOS(data, selected_pos) {
    $(".part-of-speech #pos-words").html("");
    for(var i = 0; i < data.length; i ++) {
        var html = "<div class='pos-container";
        if(selected_pos == data[i].pos) {
            html += " active";
        }
        html += "' onclick='getSynset(this, \"" + data[i].id + "\");'>";
        html += data[i].pos + ". " + data[i].name;
        html += "</div>";
        $(".part-of-speech #pos-words").append(html);
    }
}

// populate bag of words for this heading onto vis
function populateBOW(data, quick_search) {
    $(".word-box #heading-words").html("");
    // add new keywords from synset
    for(var i = 0; i < data.length; i ++) {
        var html = "<div class='term-container text-center";
        if(data[i]["enable"]) {
            if(quick_search) {
                html += "' onclick='window.location.href=\"/analyzer?quicksearch=" + data[i]["id"] + "\"');'";
            } else {
                html += "' onclick='drawKeyword(\"" + data[i]["name"] + "\", \"" + data[i]["heading_id"] + "\");'";
            }
        } else {
            html += " no-click'";
        }
        html += ">" + data[i]["name"] + "</div>";
        $(".word-box #heading-words").append(html);
    }
}

// what happens when a heading is selected to be the main node
function reorderVis() {
    $.ajax({
        type:"GET"
        , url: "/oht/tier/" + $("#modal-tier-index").val()
        , success: function(data) {
            home_tier = data.home;
            parent_tier = data.parent;
            child_tier = data.child;
            $("#add-term").click();
        }
    });
}

// what happens when a keyword is clicked in search dialog vis
function keywordClicked(d) {
    var new_tier_index = d.data.parent;
    var $target = $("#"+target, "#"+target_parent);
    var $container = $target.parent().parent();
    var weight = ($("#weight-slider").val()-1) * 0.25;
    var vis_size = min_size + (add_size * weight);
    
    // save relevant identifiers to dom for later
    saveSelection($container, d.data.heading_id
        , $("#weight-slider").val(), d.data.name);

    // draw the mini-vis to the dom element
    createNewVis("#search-term-box #"+target_parent, target, "/oht/"
        , new_tier_index, vis_size, vis_size, weight
        , false, false, false, d.data.heading_id);

    $target.attr("tier-index", new_tier_index);

    // highlight what was just changed for visual feedback
    animate("select", $("#"+target_parent).parent());
}

// make sure relevant search items are saved to dom
function saveSelection($container, heading_id, weight, name) {
    $(".term-heading-id", $container).val(heading_id);
    $(".term-heading-weight", $container).val(weight);
    $(".term-heading", $container).html(name);
}

// take saved dom elements and get new document results
function search(search_id) {
    var keyword_list = [];
    var n = 0;
    // loop through search terms in dom
    $("#search-term-box .term-container").each(function(i) {
        n++;
        if($(this).hasClass("custom-keyword")) {
            keyword_list.push( {
                "heading_id": $(".custom-keyword-heading", $(this)).attr("heading-id"),
                "keyword": $(".custom-keyword-heading", $(this)).html(),
                "weight": $(".custom-keyword-weight", $(this)).val()-1,
                "order": i+1
            });
        }
    });
    data = { "keyword_list":keyword_list };
    if(search_id) {
        data["search_id"] = search_id;
    }

    if(n == 0) return;
    getSearchResults(data);
    getJournalCount(data);
}

function getSearchResults( data ){
    $.ajax({
        url: "search"
        , contentType: "application/json"
        , data: JSON.stringify(data)
        , dataType: "json"
        , type: "POST"
        , success: function(data) {
            showSearchResults(data);
        }
    });
}

// get journal distribution of erudit
function getJournalCount( data, svg_path="#search-count" ) {
    var post_data = JSON.stringify({"keyword_list": []});
    if(typeof(data) != "undefined" && data != null) {
        post_data = JSON.stringify(data);
    }
    $.ajax({
        url: "erudit/journal_count"
        , contentType: "application/json"
        , data: post_data
        , dataType: "json"
        , type: "POST"
        , success: function(data) {
            drawJournalCount(data, svg_path);
        }
    });
}

// format and display search results
function showSearchResults( data ) {
    $("#search-result-container .doc").remove();
    for(i in data) {
        var $format = $("<div class='doc'> \
            <h3>ARTICLE</h3>\
            <div class='doc-title'></div>\
            <div class='doc-author'></div>\
            <div class='doc-cite'></div>\
            <h3>TOP KEYWORDS</h3>\
            <ul class='doc-term' id='doc-topic'></ul>\
            <h3>SEARCH TERMS</h3>\
            <ul class='doc-term' id='doc-people'></ul>\
        </div>");

        var doc = data[i];
        $format.attr("id", doc.id);
        $("#search-result-container").append($format);
        var $container = $(".doc#" + doc.id);
        $(".doc-title", $container).html( doc.title );
        $(".doc-author", $container).html( doc.author );
        $(".doc-cite", $container).html( doc.citation );

        // insert topics
        var n = 0;
        for(y in doc.topiclist) {
            var topic = doc.topiclist[y];
            if(topic.dist < 0.1) continue;
            var dist = topic.dist * 100;
            // var $docterm = $("<li><a id='" + topic.id 
            //     + "' onclick='drawSearchTerm(\"" + topic.tier_index 
            //     + "\", \"" + topic.heading_id + "\",\"" + topic.heading 
            //     + "\");' class='search-term'>" + topic.thematicheading 
            //     + " | " + topic.heading + " ( " + dist.toFixed(2) 
            //     + " % )</a></li>");
            var $docterm = $("<li><a id='" + topic.id 
                + "' onclick='drawKeyword(\"" + topic.name+ "\",\""
                + topic.heading_id + "\");' class='search-term'>" 
                + (++n) + ". "+ topic.name 
                + "</a></li>");
            $("#doc-topic", $container).append($docterm);
        }
    }
}

// set weight slider bar to a specific value
function setWeightValue(weight) {
    var dist = ((weight-1) * 25);
    $("#search-dialog .slider .slider-handle").attr("aria-valuenow", weight);
    $("#search-dialog .slider .slider-handle").css("left", dist + "%");
    $("#search-dialog .slider .slider-track .slider-selection").css("width", dist + "%");
    $("#search-dialog .slider .slider-track .slider-track-high").css("width", (1-dist) + "%");
    
    // deselect all ticks
    var $ticks = $("#search-dialog .slider .slider-tick-container .slider-tick");
    $ticks.removeClass("in-selection");
    
    // select all ticks up to the weight we want
    for(var i = 0; i < weight; i++) {
        $($ticks[i]).addClass("in-selection");
    }

    // make sure to set meta values
    $("#weight-slider").val(weight);
    $("#weight-slider").attr("data-value", weight);
}

// handle animations here so we can reuse
function animate(animation, $target) {
    switch(animation) {
        case "select":
            // highlight this box for visual feed back of changes
            $target.removeClass("selected");        
            $target.addClass("changed");
            setTimeout(function() {
                $target.removeClass("changed");
            }, 500);
            break;
    }
}