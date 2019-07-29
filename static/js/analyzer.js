/******************************************************************************
 * analyzer.js
 * Miscellaneous functions for the analyzer page that mostly have to do with
 * display or positioning for in-page interactions. If you are looking for
 * functions that involve toggling a certain window, it is probably here.
 * Last updated: 07/01/2018
 *****************************************************************************/

let searching = true, peeking = false, keyword_searching = true; // toggle modes
let target = ""; // retain which element we are editting
let target_parent = ""; // element parent
let target_index = ""; // element tier index
let type_timeout; // interval that listens for last keypress
let vis_width = $("#search-dialog-main").width();
let last_heading = "";
let selected_heading = "";



// open or close keyword search dialog
function toggleKeywordDialog() {
    if(keyword_searching) {
        $("#search-keyword-dialog").css("left", -$(window).width()-75);
        keyword_searching = false;
        $("#search-keyword-box").hide();
        $("#search-keyword").val("");
    } else {
        if(searching) {
            toggleSearchDialog();
        }
        $("#search-keyword-box").show();
        $("#search-keyword-dialog").css("left", 0);
        keyword_searching = true;
    }
}

// open or close the search dialog
function toggleSearchDialog() {
    if(searching) {
        $("#journal-count").css({
            "right": journal_count_margin
        });
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
        $("#search-keyword-box").hide();
    } else {
        if(!journal_count_minimized) {
            redrawJournalCount(true);
        }
        $("#journal-count").css({
            "right": -($(window).width()*journal_size_ratio)+journal_count_margin
        });
        if(keyword_searching) {
            toggleKeywordDialog();
        }
        // need to open
        $("#search-dialog").css("left", 0);
        $("#search-result-container").css({
            "left": $("#search-dialog").width(),
            "width": "30vw",
            "padding-left": "0",
            "padding-right": "0"
        });
        searching = true;
        $("#search-keyword-box").show();
    }
}

// Toggle document result view during search
function togglePeek() {
    if(searching) {
        // only relevant when search dialog is open
        let result_offset = $(window).width()-$("#search-result-container").width();
        let search_offset = ($("#search-dialog").width()+$("#search-result-container").width()) - $(window).width();
        if(!journal_count_minimized) redrawJournalCount(true);
        if(peeking) {
            // need to close
            $("#search-dialog").css("left", 0);
            $("#search-dialog svg").css("padding-left", 0);
            $("#search-dialog-title").css("margin-left", 0);
            $("#search-dialog .slider").css("margin-left", 0);
            $("#search-result-container").css("left", $("#search-dialog").width());
            $("#journal-count").css({
                "right": -($(window).width()*journal_size_ratio)+journal_count_margin
            });
            peeking = false;
        } else {
            // need to open
            $("#search-dialog").css("left", -(search_offset));
            $("#search-dialog svg").css("padding-left", search_offset/2);
            $("#search-dialog-title").css("margin-left", search_offset/2);
            $("#search-dialog .slider").css("margin-left", search_offset/2);
            $("#search-result-container").css("left", result_offset);
            $("#journal-count").css({
                "right": journal_count_margin
            });
            peeking = true;
        }
    }
}

// format and display search results
function showSearchResults( data ) {
    $("#search-result-container .doc").remove();
    if(data.length == 0) {
        let $format = $("<div class='doc'>Sorry, no search results found.</div>");
        $("#search-result-container").append($format);
        return;
    }
    search_terms = getSearchTerms(true);
    for(i in data) {
        let $format = $("<div class='doc'> \
            <h3>ARTICLE</h3>\
            <div class='doc-title'></div>\
            <div class='doc-author'></div>\
            <div class='doc-cite'></div>\
            <h3>KEYWORDS</h3>\
            <ul class='doc-term' id='doc-topic'></ul>\
        </div>");

        let doc = data[i];
        let doctitle = doc.title;
        // add a link if we have one
        if(doc.uri !== undefined) {
          doctitle = "<a href='https://id.erudit.org/iderudit/" + doc.uri + "'>"
            + doc.title + " <i class='fa fa-link fa-1'></i></a>";
        }
        $format.attr("id", doc.id);
        $("#search-result-container").append($format);
        let $container = $(".doc#" + doc.id);
        $(".doc-title", $container).html( doctitle );
        $(".doc-author", $container).html( doc.author );
        $(".doc-cite", $container).html( doc.citation );

        // insert topics
        let n = 0;
        for(y in doc.topiclist) {
            let topic = doc.topiclist[y];
            if(topic.dist < 0.1) continue;
            let dist = topic.dist * 100;
            let html = "<li><a id='" + topic.id + "' onclick='drawKeyword(\""
            + topic.name+ "\",\""+ topic.heading_id + "\",\"" + topic.tier_index
            +  "\", true, \"" + topic.id + "\");' data-keyword='"
            + topic.name + "' class='search-term";
            let topic_name = topic.name.normalize('NFD').replace(/[\u0300-\u036f]/g, "").toLowerCase();
            if(topic.is_keyword || $.inArray(topic_name,search_terms) != -1) {
                topic.is_keyword = 1;
                html += " existent";
            }
            html += "'>" + (++n) + ". "+ topic.name
            + "</a></li>";
            let $docterm = $(html);
            $("#doc-topic", $container).append($docterm);
        }
        let has_keywords = false;
        let has_missing = false;
        let last_rank = 5;
        let list_id = "#doc-topic";
        let top_keywords = [];
        $.each($("#doc-topic a", $container), function() {
            top_keywords.push($(this).data("keyword").normalize('NFD').replace(/[\u0300-\u036f]/g, "").toLowerCase());
        })
        for(y in doc.keywordlist) {
            let topic = doc.keywordlist[y];
            let topic_name = topic.name.normalize('NFD').replace(/[\u0300-\u036f]/g, "").toLowerCase();
            let html = "<li><a id='" + topic.id + "' class='search-term ";
            if($.inArray(topic_name, top_keywords) != -1) continue;
            if(topic.rank) {
                if(!has_keywords) {
                    has_keywords = true;
                }
                html = "<li>";
                if((topic.rank - last_rank) > 1) html += "<span>...</span>";
                html += "<a id='" + topic.id + "' class='search-term ";
                html += "existent' onclick='forceIncludeTerm(\"" + topic.name + "\", \""
                + topic.heading_id + "\", \"" + topic.id + "\");'>" + (topic.rank) + ". ";
                last_rank = topic.rank;
            } else {
                if(!has_missing) {
                    $(list_id, $container).append("<li><a class='see-all-terms' \
                    onclick='showDocumentKeywords(\"" + doc.id + "\",\"" + doc.title
                    + "\");'>view more &raquo;</a></li>")
                    has_missing = true;
                    $container.append($("<h3>MISSING TERMS</h3><ul class='doc-term' id='doc-missing-term'></ul>"));
                    list_id = "#doc-missing-term";
                }
                html += "non-existent' onclick='forceIncludeTerm(\"" + topic.name + "\", \""
                + topic.heading_id + "\", \"" + topic.id + "\");'>"
            }
            html += topic.name + "</a></li>";
            $(list_id, $container).append($(html));
        }
    }
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

// open up the exploration tool at a specific heading
function openExploreVis(heading_id) {
    if(heading_id == selected_heading) return;
    home_tier = heading_id;
    $("#add-term").click();
    if(heading_id != selected_heading) {
        last_heading = selected_heading;
        selected_heading = heading_id;
    }
    headingClicked({"data":{"heading_id":heading_id}});
}

// open up the keyword search results window
function openSearchResultVis(elem) {
    $("#search-keyword-container .keyword-container").remove();
    $(".load-keyword").show();
    $(".no-keyword").hide();
    let keyword = $(".custom-keyword-heading", elem).html();
    // toggle functionality, make sure to close other windows first
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
    $("#search-keyword").val(keyword);

    // call back for clicking on a keyword in the query bar
    let cb_keyword = function() {
        let heading_id = $(this).attr("heading-id");
        openExploreVis(heading_id);
    };

    getKeywordList(keyword, cb_keyword);
}

// set custom keyword option in keyword dialog
function setKeyword(keyword) {
    $("#search-keyword-container .keyword-heading").html(keyword.slice(0,24));
}
