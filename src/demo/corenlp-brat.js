function annotate() {
  text = document.getElementById("text").value;
  fetch('http://nlp.biu.ac.il/~lazary/syntax_extractor/?text=' + text)
    .then(function(response) {
      return response.text()
    }).then(function(body) {
      // document.body.innerHTML = body
      // alert(body)
      out = document.getElementById("out-text");
      out.innerHTML = body[0];

      out = document.getElementById("out-text-baseline");
      out.innerHTML = body[1];
      // out.type = 'text';
    })
};

