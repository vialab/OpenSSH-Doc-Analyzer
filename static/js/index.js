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
    console.log(data);
    for(var i=0; i < data.searches.length; i++) {
        $("#search-list").append("<div class='recent-doc' data-dochashid='" 
        + data.searches[i].dochashid + "'><div class='term-heading'>" 
        + data.searches[i].name + "</div>\
        </div>");
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
}