var searching = true;
var target = "";
$("svg").click(function() {
    if(!searching) {
        toggleSearchDialog();
        target = $(this).attr("id");
        createNewVis("#search-dialog", "search-dialog-vis", "/oht/", $(this).attr("tier-index"), $(window).width(),$(window).height()-90, true, true, true, keywordClicked);
    }
});

$(document).keyup(function(e) {
    if(!searching) {        
        return;
    }
    if (e.keyCode === 27) {
        toggleSearchDialog();
    }
});

$(document).ready(function() {
    toggleSearchDialog();
});

function toggleSearchDialog() {
    if(searching) {
        $("#search-dialog").css("top", $(window).height()+75);
        $("#page-content .row").show();
        searching = false;
    } else {
        $("#search-dialog").css("top", 0);
        $("#page-content .row").hide();
        searching = true;
    }
}

function keywordClicked(d) {
    var new_tier_index = d.data.parent;
    var new_target = "mini-"+new_tier_index;
    var $target = $("#"+target);

    createNewVis("#search-term-box", target, "/oht/", new_tier_index, 75, 75, false, false, false);
    $target.attr("tier-index", new_tier_index);
    $target.attr("id", new_target);
    toggleSearchDialog();

    d3.select("#"+target)
        .transition().duration(0)
            .style("background", "white")
        .transition().duration(500)
            .style("background", "yellow")
        .transition().delay(500).duration(500)
            .style("background", "white");
}