$(document).ready(function() {
    $("#search-keyword-container").hide();
    $("#search-keyword-home").on("input click", function() {
        var keyword = $(this).val();
        if(keyword != "") {
            $("#search-keyword-container").show();
        } else {
            $("#search-keyword-container").hide();        
        }
    });

    $.ajax({
        url: "/history"
        , success: function(data) {showSearchHistory(data);}
    });
});

function showSearchHistory(data) {
    for(var i=0; i < data.searches.length; i++) {
        var search_id = data.searches[i].search_id;
        $("#search-list").append("<div class='recent-search' data-searchid='" 
            + search_id + "'><div class='search-date'>" 
            + data.searches[i].date + "</div></div>");
            
        for(var k=0; k < data.searches[i].terms.length; k++) {
            var search_term = "";
            var is_heading = false;
            var data_format = "";
            var search_term, tier_index, heading_id, tier_id, svg_path;
            if(data.searches[i].terms[k].keyword) {
                search_term = data.searches[i].terms[k].keyword;
                data_format = "<div class='recent-term'><div class='term-heading'>" 
                + search_term + "</div>\
                </div>";
            } else {
                is_heading = true;
                search_term = data.searches[i].terms[k].heading;
                tier_index = data.searches[i].terms[k].tier_index;
                heading_id = data.searches[i].terms[k].heading_id;
                tier_id = tier_index.replace(/\./g, "-");
                var svg_path = "recent-" + tier_id;
                svg_path += "-" + $("[id^=" + svg_path + "]").length.toString();
                data_format = "<div class='recent-term' id='" + svg_path + "'><div class='term-heading'>" 
                    + search_term + "</div>\
                    </div>"
            }
            $("#search-list .recent-search[data-searchid='" + search_id + "']")
                .append(data_format);
            
            if(is_heading) {
                // draw mini-vis to this element
                createNewVis("#"+svg_path, "mini-" + tier_id
                    , "/oht/", tier_index, min_size, min_size, 0, false, false, false, heading_id);
                
            }
        }
    }

    if(data.searches.length > 0) {
        $("#recent-search-list").show();
    }

    for(var i=0; i < data.documents.length; i++) {
        $("#doc-list").append("<div class='recent-doc' data-dochashid='" 
        + data.documents[i].dochashid + "'><div class='term-heading'>" 
        + data.documents[i].name + "</div>\
        </div>");
    }

    if(data.documents.length > 0) {
        $("#recent-doc-list").show();
    }

    $("#doc-list .recent-doc").on("click", function() {
        window.location.href = "/analyzer?dochashid=" + $(this).data("dochashid");
    });

    $("#search-list .recent-search").on("click", function() {
        window.location.href = "/analyzer?searchid=" + $(this).data("searchid");
    });
}