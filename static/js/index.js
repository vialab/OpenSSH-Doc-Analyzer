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
            + search_id + "'></div>");
            
        for(var k=0; k < data.searches[i].terms.length; k++) {
            var search_term = "";
            if(data.searches[i].terms[k].keyword) {
                search_term = data.searches[i].terms[k].keyword;
            } else {
                search_term = data.searches[i].terms[k].headingid;                
            }
            $("#search-list .recent-search[data-searchid='" + search_id + "']")
                .append("<div class='recent-doc'><div class='term-heading'>" 
                    + search_term + "</div>\
                    </div>");
        }
    }

    for(var i=0; i < data.documents.length; i++) {
        $("#doc-list").append("<div class='recent-doc' data-dochashid='" 
        + data.documents[i].dochashid + "'><div class='term-heading'>" 
        + data.documents[i].name + "</div>\
        </div>");
    }

    $("#doc-list .recent-doc").on("click", function() {
        window.location.href = "/analyzer?dochashid=" + $(this).data("dochashid");
    });

    $("#search-list .recent-search").on("click", function() {
        window.location.href = "/analyzer?searchid=" + $(this).data("searchid");
    });
}