/******************************************************************************
 * events.js
 * Event listeners and handlers
 * * Last updated: 07/01/2018
 *****************************************************************************/

$(document).ready(function() {
    toggleKeywordDialog();
    toggleSearchDialog();
    // instantiate drag and drop elems
    $("#search-term-box").sortable({
        items: ".term-container"
    });
    $("#modal-synset").modal({show:false});
    $("#weight-slider").slider();
    let search_id = getParameterByName("searchid");
    let quick_search = getParameterByName("quicksearch");
    let heading_id = getParameterByName("headingid");
    let tier_index = getParameterByName("tierindex");
    // let dochash_id = getParameterByName("dochashid");
    if(quick_search) {
        if(heading_id) {
            openExploreVis(heading_id);
        } else {
            drawKeyword(quick_search, "");
        }
    } else if(search_id) {
        recoverSearch(search_id);
        return;
    } else {
      search();
    }
    if($(".overflow-arrow").length > 0) toggleScrollArrow();
    updateJournalCount();
});

// whenever a vis is clicked, open up our search dialog
$(document).on("click", ".term-vis svg", function() {
    let $parent = $(this).parent().parent();
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
    let vis_height = $(window).height()-$("#search-term-container").height();
    let heading_id = $(".term-heading-id", $parent).val();
    selected_heading = heading_id;
    createNewVis("#search-dialog", "search-dialog-vis", "/oht/"
        , target_index, vis_width, vis_height, headingClicked);

    // set up the weight slider bar to match selection
    let weight = $(".term-heading-weight", $parent).val();
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
// peek at the current search results
$("#search-dialog").on("click", function() {
    if(peeking) togglePeek();
});

// add a new term
$("#add-term").on("click", function() {
    // draw vis of current tier in search dialog
    let vis_height = $(window).height()-$("#search-term-container").height()-120;
    d3.select("#search-dialog-vis").remove();
    d3.select("#search-dialog-vis-parent").remove();
    d3.select("#search-dialog-vis-child").remove();
    createNewVis("#search-dialog-main", "search-dialog-vis-parent", "/oht/"
        , home_tier, vis_width, vis_height, headingClicked);
    searching = false;
    selected_heading = "";
    toggleSearchDialog();
});

// if we resize the screen, close the search dialog and adjust elements
$(window).on("resize", function() {
    searching = true;
    keyword_searching = true;
    toggleSearchDialog();
    toggleKeywordDialog();
});

$("#search-keyword, #search-keyword-home").on("input click", function() {
    let keyword = $(this).val();
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
    if(type_timeout) {
        $("#search-keyword-container .keyword-container").remove();
        clearTimeout(type_timeout);
    }

    let cb_keyword = function() {
        let heading_id = $(this).attr("heading-id");
        openExploreVis(heading_id);
    };

    if($(this).attr("id") == "search-keyword-home") {
        cb_keyword = function() {
            window.location.href = "/analyzer?quicksearch="
                + $(".keyword-heading", this).html() + "&headingid="
                + $(this).attr("heading-id") + "&tierindex="
                + $(this).attr("tier-index");
        };
    }

    type_timeout = setTimeout(function() {
        getKeywordList(keyword, cb_keyword);
    }, 1000);
});

$(document).keyup(function(e) {
    // doesn't matter if search dialog closed
    if(!searching && !keyword_searching && journal_count_minimized) {
        return;
    }
    if (e.keyCode === 27) { // ESC key
        if(!journal_count_minimized) {
            redrawJournalCount(true);
            return;
        }
        if(searching) {
            toggleSearchDialog();
        }
        if(keyword_searching) {
            toggleKeywordDialog();
        }
    }
});

// hack to capture scroll event without jquery delegation
document.addEventListener("scroll",function(event) {
    if(event.target.id === "search-term-box") {
        toggleScrollArrow();
    }
}, true);
