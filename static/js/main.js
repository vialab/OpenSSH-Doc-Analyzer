var search_terms = {};

function addToSearch( topic_id, topic_name ) {
    if(topic_id in search_terms || Object.keys(search_terms).length >= 5) {
        return;
    } else {
        search_terms[topic_id] = topic_name;
        $("#search-box table tbody").append("<tr><td>" + topic_name + "</td><td onclick='removeFromSearch(this, \""+topic_id+"\")'>x</td></tr>");
        $("#search-box").addClass("slategray");
    }
}

function removeFromSearch(elem, topic_id ) {
    $(elem).parent().remove();
    if(topic_id in search_terms) {
        delete search_terms[topic_id];
    } else {
        return;
    }
    if(Object.keys(search_terms).length==0) {
        $("#search-box").removeClass("slategray");
    }
}

// function search() {
//     var topics = Object.keys(search_terms);
//     var url = "/explore"
//     for(var i = 0; i < topics.length; i++) {
//         if(i > 0) {
//             url += "+";
//         } else {
//             url += "/";
//         }
//         url += topics[i];
//     }
//     window.location.href = url;
// }

function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}