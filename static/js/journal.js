/******************************************************************************
 * journal.js
 * Miscellaneous functions for the /journal page
 * * Last updated: 07/01/2018
 *****************************************************************************/

$(document).ready(function() {
    $("#search-keyword-container").hide();
    $("#search-keyword-home").on("input click", function() {
        // handle a quick search
        var keyword = $(this).val();
        // show if we typed something, hide if we erased
        if(keyword != "") {
            $("#search-keyword-container").show();
        } else {
            $("#search-keyword-container").hide();
        }
    });

    // async.ly get search history
    $.ajax({
        url: "/history"
        , success: function(data) {showSearchHistory(data);}
    });
});

// display search history based off ip address on main page
// this is done asynchoronously initiated by document.ready function
function showSearchHistory(data) {
    // first handle historical search queries
    for(var i=0; i < data.searches.length; i++) {
        var search_id = data.searches[i].search_id;
        // create this container identifiable through search id
        $("#search-list").append("<div class='recent-search' data-searchid='"
            + search_id + "'><div class='search-date'>"
            + data.searches[i].date + "</div></div>");
        // then let's make a box for every search term for this search id
        for(var k=0; k < data.searches[i].terms.length; k++) {
            var search_term = "";
            var is_heading = false;
            var data_format = "";
            var search_term, tier_id, svg_path, tier_index="NA";
            search_term = data.searches[i].terms[k].keyword;
            if(data.searches[i].terms[k].tier_index) {
              tier_index = data.searches[i].terms[k].tier_index;
            }
            tier_id = tier_index.replace(/\./g, "-");
            var svg_path = "recent-" + tier_id;
            svg_path += "-" + $("[id^=" + svg_path + "]").length.toString();
            data_format = "<div class='recent-term' id='" + svg_path + "'><div class='term-heading'>"
                + search_term + "</div></div>";

            let $box = $(data_format);
            // add box to container
            $("#search-list .recent-search[data-searchid='" + search_id + "']")
                .append($box);
            drawTier($box, tier_index);
        }
    }
    // make sure we display the list only when we have to
    if(data.searches.length > 0) {
        $("#recent-search-list").show();
    }

    // now handle documents
    for(var i=0; i < data.documents.length; i++) {
        // create a box for each document with the document name as text
        $("#doc-list").append("<div class='recent-doc' data-dochashid='"
        + data.documents[i].dochashid + "'><div class='term-heading'>"
        + data.documents[i].name + "</div>\
        </div>");
    }

    // only display recent docs if we have to
    if(data.documents.length > 0) {
        $("#recent-doc-list").show();
    }

    // make boxes clickable and redirect to analyzer page to recocer
    $("#doc-list .recent-doc").on("click", function() {
        if(window.location.pathname == "/journal") {
            window.location.href = "/journal/analyzer?dochashid=" + $(this).data("dochashid");
        } else {
            window.location.href = "/analyzer?dochashid=" + $(this).data("dochashid");
        }
    });

    $("#search-list .recent-search").on("click", function() {
        window.location.href = "/analyzer?searchid=" + $(this).data("searchid");
    });
}
