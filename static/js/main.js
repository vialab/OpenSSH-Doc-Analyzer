var search_terms = {};

function runIntroTour() {
  let steps = [];
  if(searching) {
    toggleSearchDialog();
  }
  // hints for the main page
  if($("#search-keyword-home").length > 0) {
      steps.push({
        intro: "Search for a keyword."
      , element: "#search-keyword-home"
    });
  }
  if($("#search-suggestion").length > 0) {
      steps.push({
        intro: "Keyword search results will show up here."
      , element: "#search-suggestion"
    });
  }
  if($("#recent-search-history").length > 0) {
      steps.push({
        intro: "If you have had any recent searches, they will appear here."
      , element: "#recent-search-history"
    });
  }
  if($(".recent-search").length > 0) {
      steps.push({
        intro: "You can return to recent searches by clicking on them."
      , element: ".recent-search"
    });
  }
  if($("#analyze-doc-form").length > 0) {
      steps.push({
        intro: "Uploading a document here will extract the keywords that have relevant search results."
      , element: "#analyze-doc-form"
    });
  }
  // hints for the analyzer
  if($("#search-term-box").length > 0) {
      steps.push({
        intro: "Search terms within your query go here."
      , element: "#search-term-box"
    });
  }
  if($(".term-container").length > 0) {
      steps.push({
        intro: "Here is a search term that is part of your query."
      , element: ".term-container"
    });
  }
  if($("#add-term").length > 0) {
      steps.push({
        intro: "Pressing the add term button will open the visualization page to search for more terms."
      , element: "#add-term"
    });
  }
  if($("#search-btn").length > 0) {
      steps.push({
        intro: "Once you're happy with your search terms, press this button to search for results."
      , element: "#search-btn"
    });
  }
  if($("#search-count").length > 0) {
      steps.push({
        intro: "Click this widget to view the distribution of your search results across the various journals in the corpus."
      , element: "#search-count"
    });
  }
  if($(".doc").length > 0) {
      steps.push({
        intro: "This is a relevant document as part of your search results."
      , element: ".doc"
    });
  }
  if($(".doc-term").length > 0) {
      steps.push({
        intro: "Here is a list of the top keywords for this document."
      , element: ".doc-term"
    });
  }
  if($(".search-term.existent").length > 0) {
      steps.push({
        intro: "Highlighted terms are the terms from your search query."
      , element: ".search-term.existent"
    });
  }
  if($(".see-all-terms").length > 0) {
      steps.push({
        intro: "Click here to view all keywords relevant for this document."
      , element: ".see-all-terms"
    });
  }
  if($("#doc-missing-term").length > 0) {
      steps.push({
        intro: "Terms that were part of your search query, but do not exist in this document are listed here. Clicking on them will toggle the force inclusion feature for the next time you run your search."
      , element: "#doc-missing-term"
    });
  }
  steps.push({
    intro: "That's it! I hope you're on your way to learn more about the Erudit corpus."
  });
  introJs("body").setOptions({steps:steps}).start();
}

function addToSearch( topic_id, topic_name ) {
    if(topic_id in search_terms || Object.keys(search_terms).length >= 5) {
        return;
    } else {
        search_terms[topic_id] = topic_name;
        $("#search-box table tbody").append("<tr><td>" + topic_name
            + "</td><td onclick='removeFromSearch(this, \""
            + topic_id+"\")'>x</td></tr>");
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

// get a query string parameter value by it's name
function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

function setCookie(name, value, days) {
  var expires = "";
  if (days) {
    var date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function getCookie(name) {
  var nameEQ = name + "=";
  var ca = document.cookie.split(';');
  for (var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
}

$(document).ready(function() {
  $("#language-btn").click( function(event) {

    let supportedLanguages = ['en'];
    // Get languages this site supports
    $.ajax({
      type: 'GET',
      url: '/api/languages',
      async: false,
      success: function(data){
        supportedLanguages = data;
      }
    });

    lang = getCookie('selected-language') || 'en'
    
    let index = supportedLanguages.indexOf(lang)
    if (index !== -1) supportedLanguages.splice(index, 1);
    if (supportedLanguages.length<1) { return; }
  
    if (supportedLanguages.length == 1) {
      lang = supportedLanguages[0]

      setCookie('selected-language', lang)
      location.reload();
    } else {
      // TODO spawn a drop-down list of language selectors
    }
  });
});