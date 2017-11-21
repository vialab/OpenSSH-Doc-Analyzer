var searching = true, peeking = false;
var target = "";
var target_index = "";

$("svg").click(function() {
    var $parent = $(this).parent().parent();
    $(".term-container").removeClass("selected");
    $parent.addClass("selected");
    $("#search-dialog-title").html($(".term-heading", $parent).html());
    if(!searching) {
        toggleSearchDialog();
    }
    target = $(this).attr("id");
    target_index = $(this).attr("tier-index");
    var vis_height = $(window).height()-$("#search-term-container").height()-80;
    var heading_id = $(".term-heading-id", $parent).val();
    
    createNewVis("#search-dialog", "search-dialog-vis", "/oht/"
        , target_index, $("#search-dialog").width()-2, vis_height, 1
        , true, true, true, keywordClicked, heading_id);
});

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
    $("#search-term-box").sortable({
        items: ".term-container"
    });
});

function toggleSearchDialog() {
    if(searching) {
        $("#search-dialog").css("left", -$(window).width()-75);
        $("#search-result-container").css("left", 0);
        $("#search-result-container").css("width", "100vw");
        searching = false;
        peeking = false;
        $(".term-container").removeClass("selected");    
    } else {
        $("#search-dialog").css("left", 0);
        $("#search-result-container").css("left", $("#search-dialog").width());
        $("#search-result-container").css("width", "30vw");
        searching = true;
    }
}

function togglePeek() {
    if(searching) {
        var result_offset = $(window).width()-$("#search-result-container").width();
        var search_offset = ($("#search-dialog").width()+$("#search-result-container").width()) - $(window).width();
        if(peeking) {
            $("#search-dialog").css("left", 0);
            $("#search-result-container").css("left", $("#search-dialog").width());
            peeking = false;
        } else {
            $("#search-dialog").css("left", -(search_offset));
            $("#search-result-container").css("left", result_offset);
            peeking = true;
        }
    }
}

function keywordClicked(d) {
    var new_tier_index = d.data.parent;
    var $target = $("#"+target);
    var weight = parseFloat($target.attr("weight"));
    var vis_size = min_size + (add_size * weight);

    $(".term-heading-id", $target.parent().parent()).val(d.data.heading_id);
    $(".term-heading", $target.parent().parent()).html(d.data.name);

    createNewVis("#search-term-box", target, "/oht/"
        , new_tier_index, vis_size, vis_size, weight, false, false, false);
    $target.attr("tier-index", new_tier_index);
    toggleSearchDialog();

    d3.select("#"+target)
        .transition().duration(0)
            .style("background", "white")
        .transition().duration(500)
            .style("background", "#a8d1ff")
        .transition().delay(500).duration(500)
            .style("background", "white");
}

function search() {
    var heading_list = {};
    $("#term-heading-id").each(function() {
        
    });
}