var searching = true, peeking = false;
var target = "";
var target_parent = "";
var target_index = "";

$(document).on("click", ".term-vis svg", function() {
    var $parent = $(this).parent().parent();
    $(".term-container").removeClass("selected");
    $parent.addClass("selected");
    $("#search-dialog-title").html($(".term-heading", $parent).html());
    if(!searching) {
        toggleSearchDialog();
    }
    target = $(this).attr("id");
    target_parent = $(this).parent().attr("id");
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

$("#add-term").on("click", function() {
    drawSearchTerm("1.NA.NA.NA.NA.NA.NA.1", 181456, "The world", 0);
    $("#search-term-box").sortable("destroy");
    $("#search-term-box").sortable({
        items: ".term-container"
    });
});

$(window).on("resize", function() {
    searching = true;
    toggleSearchDialog();
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
        $("#search-result-container").css({
            "left": 0,
            "width": "100vw",
            "padding-left": "2%",
            "padding-right": "2%"
        });
        $("#search-dialog svg").css("padding-left", 0);
        searching = false;
        peeking = false;
        $(".term-container").removeClass("selected");    
    } else {
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

function togglePeek() {
    if(searching) {
        var result_offset = $(window).width()-$("#search-result-container").width();
        var search_offset = ($("#search-dialog").width()+$("#search-result-container").width()) - $(window).width();
        if(peeking) {
            $("#search-dialog").css("left", 0);
            $("#search-dialog svg").css("padding-left", 0);
            $("#search-result-container").css("left", $("#search-dialog").width());
            peeking = false;
        } else {
            $("#search-dialog").css("left", -(search_offset));
            $("#search-dialog svg").css("padding-left", search_offset/2);
            $("#search-result-container").css("left", result_offset);
            peeking = true;
        }
    }
}

function keywordClicked(d) {
    var new_tier_index = d.data.parent;
    var $target = $("#"+target, "#"+target_parent);
    var weight = parseFloat($target.attr("weight"));
    var vis_size = min_size + (add_size * weight);

    $(".term-heading-id", $target.parent().parent()).val(d.data.heading_id);
    $(".term-heading", $target.parent().parent()).html(d.data.name);
    createNewVis("#search-term-box #"+target_parent, target, "/oht/"
        , new_tier_index, vis_size, vis_size, weight, false, false, false, null, d.data.heading_id);
    $target.attr("tier-index", new_tier_index);
    toggleSearchDialog();

    $("#"+target_parent).parent().removeClass("selected");        
    $("#"+target_parent).parent().addClass("changed");
    setTimeout(function() {
        $("#"+target_parent).parent().removeClass("changed");
    }, 500);
}

function search() {
    var heading_list = {};
    $("#term-heading-id").each(function() {
        
    });
}