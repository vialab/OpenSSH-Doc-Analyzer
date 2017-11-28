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
    
    var vis_height = $(window).height()-$("#search-term-container").height()-120;
    var heading_id = $(".term-heading-id", $parent).val();
    createNewVis("#search-dialog", "search-dialog-vis", "/oht/"
        , target_index, $("#search-dialog").width()-2, vis_height, 1
        , true, true, true, heading_id, keywordClicked);

    var weight = $(".term-heading-weight", $parent).val();
    setWeightValue(weight);

    $("#search-dialog .slider").css("bottom", $("#search-term-container").height() + 15);
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
    var idx = $(".term-container").length-1;
    if(idx < 0) idx = 0;
    $($(".term-container svg")[idx]).click();
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
    $("#weight-slider").slider();
});

function deleteTerm(self) {
    $(self).parent().remove();
    if(searching) {
        toggleSearchDialog();
    }
}

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
        $("#search-dialog-title").css("margin-left", 0);
        $("#search-dialog .slider").css("margin-left", 0);
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
            $("#search-dialog-title").css("margin-left", 0);
            $("#search-dialog .slider").css("margin-left", 0);
            $("#search-result-container").css("left", $("#search-dialog").width());
            peeking = false;
        } else {
            $("#search-dialog").css("left", -(search_offset));
            $("#search-dialog svg").css("padding-left", search_offset/2);
            $("#search-dialog-title").css("margin-left", search_offset/2);
            $("#search-dialog .slider").css("margin-left", search_offset/2);
            $("#search-result-container").css("left", result_offset);
            peeking = true;
        }
    }
}

function keywordClicked(d) {
    var new_tier_index = d.data.parent;
    var $target = $("#"+target, "#"+target_parent);
    var $container = $target.parent().parent();
    var weight = ($("#weight-slider").val()-1) * 0.25;
    var vis_size = min_size + (add_size * weight);

    saveSelection($container, d.data.heading_id
        , $("#weight-slider").val(), d.data.name);

    createNewVis("#search-term-box #"+target_parent, target, "/oht/"
        , new_tier_index, vis_size, vis_size, weight
        , false, false, false, d.data.heading_id);

    $target.attr("tier-index", new_tier_index);
    // toggleSearchDialog();

    animate("select", $("#"+target_parent).parent());
}

function saveSelection($container, heading_id, weight, name) {
    $(".term-heading-id", $container).val(heading_id);
    $(".term-heading-weight", $container).val(weight);
    $(".term-heading", $container).html(name);
}

function search() {
    var heading_list = [];
    $(".term-container").each(function(i) {
        heading_list.push( {
            "heading_id": $(".term-heading-id", $(this)).val(),
            "weight": $(".term-heading-weight", $(this)).val(),
            "order": i+1
        });
    });
}

function setWeightValue(weight) {
    var dist = ((weight-1) * 25);
    $("#search-dialog .slider .slider-handle").attr("aria-valuenow", weight);
    $("#search-dialog .slider .slider-handle").css("left", dist + "%");
    $("#search-dialog .slider .slider-track .slider-selection").css("width", dist + "%");
    $("#search-dialog .slider .slider-track .slider-track-high").css("width", (1-dist) + "%");
    
    var $ticks = $("#search-dialog .slider .slider-tick-container .slider-tick");
    $ticks.removeClass("in-selection");
    for(var i = 0; i < weight; i++) {
        $($ticks[i]).addClass("in-selection");
    }

    $("#weight-slider").val(weight);
    $("#weight-slider").attr("data-value", weight);
}

function animate(animation, $target) {
    switch(animation) {
        case "select":
            $target.removeClass("selected");        
            $target.addClass("changed");
            setTimeout(function() {
                $target.removeClass("changed");
            }, 500);
            break;
    }
}