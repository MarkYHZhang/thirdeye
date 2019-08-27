fetch('/channels')
  .then(function(response) {
    return response.json();
  })
  .then(function(myJson) {
    var e = document.getElementById("container");

    for(var i = 0; i < myJson.length; i++) {
        channel = myJson[i];
        const feed = document.createElement('img');
        feed.className = 'videoFeed';
        feed.src = '/video_feed?channel='+channel;
        e.appendChild(feed);
    }
  });