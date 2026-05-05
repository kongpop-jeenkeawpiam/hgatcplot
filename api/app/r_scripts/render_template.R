args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 7) {
  stop("R renderer expects input, output_dir, slug, family, width, height, and title arguments.")
}

input_path <- args[[1]]
output_dir <- args[[2]]
slug <- args[[3]]
family <- args[[4]]
width_px <- as.integer(args[[5]])
height_px <- as.integer(args[[6]])
plot_title <- args[[7]]

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
data <- read.delim(input_path, check.names = FALSE, stringsAsFactors = FALSE)
data <- type.convert(data, as.is = TRUE)

palette <- c("#2f6f73", "#d36f45", "#6f5fa8", "#d1a53c", "#4f8f5f", "#b04c6f", "#58798a", "#8a6d3b")

numeric_columns <- function(frame) {
  names(frame)[vapply(frame, is.numeric, logical(1))]
}

first_numeric <- function(frame, default = 1) {
  cols <- numeric_columns(frame)
  if (length(cols) == 0) {
    rep(default, nrow(frame))
  } else {
    frame[[cols[[1]]]]
  }
}

second_numeric <- function(frame, default = 1) {
  cols <- numeric_columns(frame)
  if (length(cols) < 2) {
    seq_len(max(nrow(frame), 1)) * default
  } else {
    frame[[cols[[2]]]]
  }
}

first_label <- function(frame) {
  if (ncol(frame) == 0) {
    character()
  } else {
    as.character(frame[[1]])
  }
}

plot_template <- function(frame, family_name, title_text) {
  op <- par(no.readonly = TRUE)
  on.exit(par(op), add = TRUE)
  par(bg = "#f7faf8", fg = "#172623", col.axis = "#314541", col.lab = "#314541", mar = c(5, 5, 4, 2))

  values <- first_numeric(frame)
  labels <- first_label(frame)

  if (family_name %in% c("pie", "set")) {
    pie(abs(values), labels = labels, col = palette, main = title_text)
  } else if (family_name %in% c("line", "area", "dual-axis")) {
    x <- seq_along(values)
    if ("x" %in% names(frame) && is.numeric(frame[["x"]])) {
      x <- frame[["x"]]
    }
    plot(x, values, type = "o", col = palette[[1]], pch = 19, lwd = 2, main = title_text, xlab = names(frame)[[1]], ylab = "value")
    if (family_name == "area") {
      polygon(c(x, rev(x)), c(values, rep(min(values), length(values))), col = adjustcolor(palette[[1]], 0.25), border = NA)
      lines(x, values, col = palette[[1]], lwd = 2)
      points(x, values, pch = 19, col = palette[[2]])
    }
    grid(col = "#d9e1dd")
  } else if (family_name %in% c("scatter", "correlation", "qq", "pca", "roc", "survival")) {
    x <- values
    y <- second_numeric(frame)
    plot(x, y, pch = 19, col = adjustcolor(palette[[1]], 0.78), main = title_text, xlab = names(frame)[[1]], ylab = names(frame)[[min(2, ncol(frame))]])
    abline(lm(y ~ x), col = palette[[2]], lwd = 2)
    grid(col = "#d9e1dd")
  } else if (family_name %in% c("distribution", "density")) {
    if ("group" %in% names(frame)) {
      boxplot(value ~ group, data = frame, col = adjustcolor(palette, 0.65), main = title_text, ylab = "value")
      stripchart(value ~ group, data = frame, vertical = TRUE, method = "jitter", pch = 19, col = "#172623", add = TRUE)
    } else {
      hist(values, col = adjustcolor(palette[[1]], 0.65), border = "white", main = title_text, xlab = "value")
    }
  } else if (family_name %in% c("heatmap", "matrix")) {
    nums <- numeric_columns(frame)
    if (length(nums) >= 2) {
      matrix_values <- as.matrix(frame[nums])
    } else {
      matrix_values <- matrix(values, nrow = max(1, floor(sqrt(length(values)))))
    }
    image(t(matrix_values[nrow(matrix_values):1, , drop = FALSE]), col = colorRampPalette(c("#3a6ea5", "#f2f1e8", "#c94c4c"))(50), axes = FALSE, main = title_text)
    box(col = "#d9e1dd")
  } else if (family_name %in% c("network", "pathway", "sequence", "maf", "epigenome", "genome")) {
    barplot(abs(values), names.arg = substr(labels, 1, 12), las = 2, col = palette, main = title_text, ylab = "value")
  } else if (family_name == "forest") {
    effects <- if ("effect" %in% names(frame)) frame[["effect"]] else values
    lows <- if ("low" %in% names(frame)) frame[["low"]] else effects * 0.85
    highs <- if ("high" %in% names(frame)) frame[["high"]] else effects * 1.15
    y <- seq_along(effects)
    plot(effects, y, xlim = range(c(lows, highs, 1), na.rm = TRUE), yaxt = "n", pch = 19, col = palette[[1]], main = title_text, xlab = "effect", ylab = "")
    segments(lows, y, highs, y, col = palette[[1]], lwd = 2)
    abline(v = 1, lty = 2, col = palette[[2]])
    axis(2, at = y, labels = substr(labels, 1, 18), las = 2)
  } else if (family_name %in% c("funnel", "hierarchy", "wordcloud", "calendar", "radar", "polar", "dumbbell", "stacked-bar", "errorbar", "bar")) {
    barplot(abs(values), names.arg = substr(labels, 1, 12), las = 2, col = palette, main = title_text, ylab = "value")
  } else {
    plot.new()
    text(0.5, 0.56, title_text, cex = 1.6, font = 2, col = "#172623")
    text(0.5, 0.45, paste("HGATCplot R renderer:", slug), cex = 1, col = "#314541")
  }
}

write_plot <- function(format_name, file_name) {
  path <- file.path(output_dir, file_name)
  if (format_name == "svg") {
    svg(path, width = width_px / 96, height = height_px / 96)
  } else if (format_name == "png") {
    png(path, width = width_px, height = height_px, res = 120)
  } else if (format_name == "tiff") {
    tiff(path, width = width_px, height = height_px, res = 120, compression = "lzw")
  } else if (format_name == "pdf") {
    pdf(path, width = width_px / 96, height = height_px / 96)
  }
  plot_template(data, family, plot_title)
  dev.off()
}

write_plot("svg", "plot.svg")
write_plot("png", "plot.png")
write_plot("tiff", "plot.tiff")
write_plot("pdf", "plot.pdf")
