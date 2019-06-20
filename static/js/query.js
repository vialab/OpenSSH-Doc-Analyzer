/******************************************************************************
 * query.js
 * Anything that has to do with the /analyzer search bar
 * * Last updated: 07/01/2018
 *****************************************************************************/

// delete a search term from dom
function deleteTerm(e) {
    $(e).parent().remove();
    if(searching) {
        toggleSearchDialog();
    }
    updateJournalCount(true);
    window.event.cancelBubble = true;
}

// take saved dom elements and get new document results
function search(search_id) {
    let keyword_list = getSearchTerms();
    if(keyword_list.length == 0) return;

    let data = { "keyword_list":keyword_list };
    if(search_id) data["search_id"] = search_id;

    getSearchResults(data);
}

// display a set of keywords in keyword dialog
function showKeywordResults(data, cb_keyword) {
    $(".load-keyword").hide();
    if(data.length == 0) {
        $(".no-keyword").show();
    }
    for(i in data) {
        let clean_tier_index = data[i][4].replace(/\./g, "-");
        let svg_path = "keyword-vis-" + clean_tier_index;
        svg_path += "-" + $("[id^=" + svg_path + "]").length.toString();
        // create the container and add to dom
        let $box = $("<div class='keyword-container' id='keyword-"
                + clean_tier_index + "' tier-index='" + data[i][4]
                +"' heading-id='" + data[i][0] + "'>\
            <div class='keyword-heading'>" + data[i][2] + "</div>\
            <div class='keyword-vis' id='" + svg_path + "'></div>\
        </div>");
        $(".custom-keyword-container").after($box);
    }
    $(".custom-keyword-container").off("click");
    $(".custom-keyword-container").on("click", function() {
        drawKeyword($(".keyword-heading").html(),"",true);
        toggleKeywordDialog();
    });

    $(".custom-keyword-container.homepage").on("click", function() {
        $(this).off("click");
        window.location.href = "/analyzer?quicksearch=" + $(".keyword-heading", this).html();
    });

    $(".keyword-container").on("click", cb_keyword);
}

// force the inclusion of a term (i.e. toggle its star ON)
function forceIncludeTerm(keyword, heading_id, id) {
    let already_used = false;
    keyword = keyword.trim().normalize('NFD').replace(/[\u0300-\u036f]/g, "").toLowerCase();
    $("#search-term-box .term-container").each(function(i) {
        let used_keyword = $(".custom-keyword-heading", $(this)).html().normalize('NFD').replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
        if(keyword == used_keyword) {
            already_used = true;
            $.each($(".star", $(this)), function() {
                toggleStar(this);
            });
        }
    });
    if(!already_used) {
        drawKeyword(keyword, heading_id, true, id);
    }
    updateJournalCount(true);
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
    if($(".overflow-arrow").length > 0) toggleScrollArrow();
    resortable();
    // we want the journal counts to show potential changes
    // whenever the search query changes
    if(draw_count) {
        updateJournalCount(true);
    }
}

// toggle our scroll indicator arrows when needed
function toggleScrollArrow() {
    let add_left = $("#add-term").offset().left;
    let search_left = $("#search-btn").offset().left;
    if(add_left > search_left-100) {
        $("#overflow-arrow-right").css("opacity",1);
    } else {
        $("#overflow-arrow-right").css("opacity",0);
    }
    if($("#search-term-box").scrollLeft() > 0) {
        $("#overflow-arrow-left").css("opacity",1);
    } else {
        $("#overflow-arrow-left").css("opacity",0);
    }
}

// scroll the search term box right
function scrollSTBox(dir) {
    let box_width = $("#search-term-box").width();
    let scroll_left = $("#search-term-box").scrollLeft();
    let page = Math.round(scroll_left / box_width);
    if(dir==1) {
        page++;
    } else if(dir==0 && page > 0) {
        page--;
    }
    $("#search-term-box").animate({
        scrollLeft: page*box_width
    });
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

// re-instantiate sortable (drag and drop) dom elements
function resortable() {
    $("#search-term-box").sortable("destroy");
    $("#search-term-box").sortable({
        items: ".term-container"
    });
}
