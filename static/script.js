$(document).ready(function () {
  // Handle form submission
  $("#convert-form").submit(function (event) {
    event.preventDefault(); // Prevent form submission

    // Show loading overlay
    $("#loading-overlay").show();

    var form = $(this);
    var url = form.attr("action");
    var formData = new FormData(form[0]);

    $.ajax({
      type: "POST",
      url: url,
      data: formData,
      processData: false,
      contentType: false,
      beforeSend: function () {
        // Show loading spinner
        $(".loading-spinner").show();
      },
      success: function (response) {
        // Hide loading spinner
        $(".loading-spinner").hide();

        // Show SQL query and results with typing animation
        updateSqlQueryText(response.sql_query);
        updateResultsText(JSON.stringify(response.results, null, 2));
      },
      error: function (error) {
        console.log(error);
      },
      complete: function () {
        // Hide loading overlay
        $("#loading-overlay").hide();
      },
    });
  });

  // Function to update SQL query text with typing animation
  function updateSqlQueryText(sqlQuery) {
    const sqlQueryElement = $("#sql-query");
    sqlQueryElement.removeClass("typing");
    sqlQueryElement.text(""); // Clear previous text

    let i = 0;
    const typingInterval = setInterval(() => {
      if (i <= sqlQuery.length) {
        sqlQueryElement.text(sqlQuery.slice(0, i));
        i++;
      } else {
        clearInterval(typingInterval);
        sqlQueryElement.addClass("typing");
      }
    }, 100);
  }

  // Function to update results text
  function updateResultsText(results) {
    $("#results").text(results);
  }

  // Handle copy button click
  $("#copy-button").click(function () {
    const resultText = $("#results").text();
    navigator.clipboard
      .writeText(resultText)
      .then(() => {
        alert("Result text copied!");
      })
      .catch((error) => {
        console.error("Error copying text:", error);
      });
  });
});
