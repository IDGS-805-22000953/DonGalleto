module.exports = {
    content: [
        "./templates/**/*.html",
        "./static/src/**/*.js",
        "./node_modules/flowbite/**/*.js"
    ],
    theme: {
      extend: {
        fontFamily: {
          adlam: ["'ADLaM Display'", "cursive"],
        },
      },
    },
    plugins: [
      require("flowbite/plugin")
    ],
  };