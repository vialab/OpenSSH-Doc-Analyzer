var searching = true, peeking = false; // toggle modes
var target = ""; // retain which element we are editting
var target_parent = ""; // element parent
var target_index = ""; // element tier index

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
    var vis_height = $(window).height()-$("#search-term-container").height()-120;
    var heading_id = $(".term-heading-id", $parent).val();
    createNewVis("#search-dialog", "search-dialog-vis", "/oht/"
        , target_index, $("#search-dialog").width()-2, vis_height, 1
        , true, true, true, heading_id, keywordClicked);

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
    // draw the search term to dom
    drawSearchTerm("1.NA.NA.NA.NA.NA.NA.1", 181456, "The world", 0);
    // re-instantiate sortable (drag and drop) dom elements
    $("#search-term-box").sortable("destroy");
    $("#search-term-box").sortable({
        items: ".term-container"
    });
    // open up search dialog to new term
    var idx = $(".term-container").length-1;
    if(idx < 0) idx = 0;
    $($(".term-container svg")[idx]).click();
});

// if we resize the screen, close the search dialog and adjust elements
$(window).on("resize", function() {
    searching = true;
    toggleSearchDialog();
});

$(document).keyup(function(e) {
    // doesn't matter if search dialog closed
    if(!searching) {        
        return;
    }
    if (e.keyCode === 27) { // ESC key
        toggleSearchDialog();
    }
});

$(document).ready(function() {
    toggleSearchDialog();
    // instantiate drag and drop elems
    $("#search-term-box").sortable({
        items: ".term-container"
    });
    $("#weight-slider").slider();
});

// delete a search term from dom
function deleteTerm(self) {
    $(self).parent().remove();
    if(searching) {
        toggleSearchDialog();
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
function search() {
    var heading_list = [];
    // loop through search terms in dom
    $(".term-container").each(function(i) {
        heading_list.push( {
            "heading_id": $(".term-heading-id", $(this)).val(),
            "weight": $(".term-heading-weight", $(this)).val(),
            "order": i+1
        });
    });
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