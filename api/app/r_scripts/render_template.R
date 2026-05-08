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

label_column <- function(frame) {
  if (ncol(frame) == 0) character() else as.character(frame[[1]])
}

plot_pie_or_set <- function(frame, title_text) {
  values <- abs(first_numeric(frame))
  pie(values, labels = label_column(frame), col = palette, main = title_text)
}

plot_line_or_area <- function(frame, family_name, title_text) {
  values <- first_numeric(frame)
  x <- if ("x" %in% names(frame) && is.numeric(frame[["x"]])) frame[["x"]] else seq_along(values)
  plot(x, values, type = "o", col = palette[[1]], pch = 19, lwd = 2, main = title_text, xlab = "x", ylab = "value")
  if (family_name == "area") {
    polygon(c(x, rev(x)), c(values, rep(min(values), length(values))), col = adjustcolor(palette[[1]], 0.25), border = NA)
    lines(x, values, col = palette[[1]], lwd = 2)
    points(x, values, pch = 19, col = palette[[2]])
  }
  grid(col = "#d9e1dd")
}

plot_scatter_family <- function(frame, title_text) {
  x <- first_numeric(frame)
  y <- second_numeric(frame)
  plot(x, y, pch = 19, col = adjustcolor(palette[[1]], 0.78), main = title_text, xlab = "x", ylab = "y")
  if (length(x) > 1 && length(unique(x)) > 1) {
    abline(lm(y ~ x), col = palette[[2]], lwd = 2)
  }
  grid(col = "#d9e1dd")
}

plot_distribution <- function(frame, family_name, title_text) {
  values <- first_numeric(frame)
  if ("group" %in% names(frame) && "value" %in% names(frame)) {
    boxplot(value ~ group, data = frame, col = adjustcolor(palette, 0.65), main = title_text, ylab = "value")
    stripchart(value ~ group, data = frame, vertical = TRUE, method = "jitter", pch = 19, col = "#172623", add = TRUE)
  } else if (family_name == "density" && length(values) > 1) {
    density_values <- density(values)
    plot(density_values, main = title_text, col = palette[[1]], lwd = 2, xlab = "value")
    polygon(density_values, col = adjustcolor(palette[[1]], 0.25), border = palette[[1]])
  } else {
    hist(values, col = adjustcolor(palette[[1]], 0.65), border = "white", main = title_text, xlab = "value")
  }
}

plot_heatmap <- function(frame, title_text) {
  nums <- numeric_columns(frame)
  if (length(nums) >= 2) {
    matrix_values <- as.matrix(frame[nums])
  } else {
    values <- first_numeric(frame)
    matrix_values <- matrix(values, nrow = max(1, ceiling(sqrt(length(values)))))
  }
  image(t(matrix_values[nrow(matrix_values):1, , drop = FALSE]), col = colorRampPalette(c("#3a6ea5", "#f2f1e8", "#c94c4c"))(50), axes = FALSE, main = title_text)
  box(col = "#d9e1dd")
}

plot_network <- function(frame, title_text) {
  if (!all(c("source", "target") %in% names(frame))) {
    stop("Network render requires source and target columns.")
  }
  nodes <- sort(unique(c(as.character(frame$source), as.character(frame$target))))
  angles <- seq(0, 2 * pi, length.out = length(nodes) + 1)[seq_along(nodes)]
  xs <- cos(angles)
  ys <- sin(angles)
  names(xs) <- nodes
  names(ys) <- nodes
  plot(xs, ys, type = "n", axes = FALSE, xlab = "", ylab = "", main = title_text, asp = 1)
  for (i in seq_len(nrow(frame))) {
    segments(xs[as.character(frame$source[i])], ys[as.character(frame$source[i])], xs[as.character(frame$target[i])], ys[as.character(frame$target[i])], col = "#9aa8a3", lwd = 1.5)
  }
  points(xs, ys, pch = 21, bg = palette[seq_along(nodes) %% length(palette) + 1], cex = 2.8, col = "white")
  text(xs, ys, labels = substr(nodes, 1, 10), cex = 0.72, col = "#172623")
}

plot_set <- function(frame, title_text) {
  values <- abs(first_numeric(frame))
  labels <- substr(label_column(frame), 1, 12)
  symbols(seq_along(values), rep(1, length(values)), circles = sqrt(values / max(values, 1)) * 0.38,
          inches = FALSE, fg = palette[seq_along(values) %% length(palette) + 1],
          bg = adjustcolor(palette[seq_along(values) %% length(palette) + 1], 0.35),
          xlab = "", ylab = "", axes = FALSE, main = title_text)
  text(seq_along(values), rep(1, length(values)), labels = labels, cex = 0.8, col = "#172623")
}

plot_hierarchy <- function(frame, title_text) {
  values <- pmax(first_numeric(frame), 0)
  labels <- substr(label_column(frame), 1, 14)
  total <- sum(values)
  if (total <= 0) total <- 1
  plot.new()
  title(title_text)
  cursor <- 0
  for (i in seq_along(values)) {
    width <- values[[i]] / total
    rect(cursor, 0.12, cursor + width, 0.88, col = adjustcolor(palette[[((i - 1) %% length(palette)) + 1]], 0.75), border = "white")
    if (width > 0.08) text(cursor + width / 2, 0.52, labels[[i]], col = "white", cex = 0.82)
    cursor <- cursor + width
  }
}

plot_pathway <- function(frame, title_text) {
  if (!all(c("pathway", "gene") %in% names(frame))) {
    plot_bar_like(frame, "bar", title_text)
    return()
  }
  pathways <- sort(unique(as.character(frame$pathway)))
  genes <- sort(unique(as.character(frame$gene)))
  px <- rep(0.24, length(pathways)); names(px) <- pathways
  py <- seq(0.85, 0.15, length.out = length(pathways)); names(py) <- pathways
  gx <- rep(0.76, length(genes)); names(gx) <- genes
  gy <- seq(0.85, 0.15, length.out = length(genes)); names(gy) <- genes
  plot.new()
  title(title_text)
  for (i in seq_len(nrow(frame))) {
    segments(px[as.character(frame$pathway[i])], py[as.character(frame$pathway[i])], gx[as.character(frame$gene[i])], gy[as.character(frame$gene[i])], col = "#9aa8a3")
  }
  points(px, py, pch = 22, bg = palette[seq_along(pathways) %% length(palette) + 1], col = "white", cex = 3.2)
  text(px, py, labels = substr(pathways, 1, 11), cex = 0.65, col = "white")
  points(gx, gy, pch = 21, bg = palette[(seq_along(genes) + 3) %% length(palette) + 1], col = "white", cex = 2.1)
  text(gx + 0.04, gy, labels = substr(genes, 1, 12), cex = 0.72, pos = 4)
}

plot_maf <- function(frame, title_text) {
  if (!all(c("gene", "sample", "mutation") %in% names(frame))) {
    plot_bar_like(frame, "bar", title_text)
    return()
  }
  genes <- sort(unique(as.character(frame$gene)))
  samples <- sort(unique(as.character(frame$sample)))
  plot(NA, xlim = c(0.5, length(samples) + 0.5), ylim = c(0.5, length(genes) + 0.5),
       xaxt = "n", yaxt = "n", xlab = "sample", ylab = "gene", main = title_text)
  axis(1, at = seq_along(samples), labels = samples, las = 2)
  axis(2, at = seq_along(genes), labels = genes, las = 2)
  for (i in seq_len(nrow(frame))) {
    x <- match(as.character(frame$sample[i]), samples)
    y <- match(as.character(frame$gene[i]), genes)
    rect(x - 0.45, y - 0.45, x + 0.45, y + 0.45, col = palette[((y - 1) %% length(palette)) + 1], border = "white")
  }
  grid(col = "#d9e1dd")
}

plot_wordcloud <- function(frame, title_text) {
  values <- first_numeric(frame)
  labels <- substr(label_column(frame), 1, 18)
  low <- min(values)
  high <- max(values)
  if (low == high) high <- low + 1
  plot.new()
  title(title_text)
  angles <- seq(0, 8 * pi, length.out = length(labels))
  radii <- seq(0, 0.38, length.out = length(labels))
  xs <- 0.5 + radii * cos(angles)
  ys <- 0.5 + radii * sin(angles)
  for (i in seq_along(labels)) {
    text(xs[[i]], ys[[i]], labels[[i]], cex = 0.8 + 1.6 * (values[[i]] - low) / (high - low),
         col = palette[((i - 1) %% length(palette)) + 1], srt = ifelse(i %% 7 == 4, 90, 0), font = 2)
  }
}

plot_forest <- function(frame, title_text) {
  effects <- if ("effect" %in% names(frame)) frame[["effect"]] else first_numeric(frame)
  lows <- if ("low" %in% names(frame)) frame[["low"]] else effects * 0.85
  highs <- if ("high" %in% names(frame)) frame[["high"]] else effects * 1.15
  y <- seq_along(effects)
  plot(effects, y, xlim = range(c(lows, highs, 1), na.rm = TRUE), yaxt = "n", pch = 19, col = palette[[1]], main = title_text, xlab = "effect", ylab = "")
  segments(lows, y, highs, y, col = palette[[1]], lwd = 2)
  abline(v = 1, lty = 2, col = palette[[2]])
  axis(2, at = y, labels = substr(label_column(frame), 1, 18), las = 2)
}

plot_bar_like <- function(frame, family_name, title_text) {
  values <- first_numeric(frame)
  labels <- substr(label_column(frame), 1, 12)
  if (family_name == "funnel") {
    order <- order(values)
    barplot(abs(values[order]), names.arg = labels[order], horiz = TRUE, las = 1, col = palette, main = title_text, xlab = "value")
  } else if (family_name == "stacked-bar" && all(c("category", "series", "value") %in% names(frame))) {
    wide <- xtabs(value ~ series + category, data = frame)
    barplot(wide, col = palette, main = title_text, ylab = "value", legend.text = TRUE, args.legend = list(bty = "n", cex = 0.75))
  } else if (family_name == "errorbar" && "error" %in% names(frame)) {
    mids <- barplot(values, names.arg = labels, las = 2, col = palette, main = title_text, ylab = "value")
    arrows(mids, values - frame$error, mids, values + frame$error, angle = 90, code = 3, length = 0.05, col = "#172623")
  } else {
    barplot(abs(values), names.arg = labels, las = 2, col = palette, main = title_text, ylab = "value")
  }
}

plot_genome_or_sequence <- function(frame, family_name, title_text) {
  values <- first_numeric(frame)
  positions <- if ("position" %in% names(frame)) frame[["position"]] else seq_along(values)
  plot(positions, values, type = "h", lwd = 4, col = palette[seq_along(values) %% length(palette) + 1], main = title_text, xlab = "position", ylab = "value")
  points(positions, values, pch = 19, col = palette[[2]])
  grid(col = "#d9e1dd")
}

plot_template <- function(frame, family_name, title_text) {
  op <- par(no.readonly = TRUE)
  on.exit(par(op), add = TRUE)
  par(bg = "#f7faf8", fg = "#172623", col.axis = "#314541", col.lab = "#314541", mar = c(5, 5, 4, 2))

  if (family_name %in% c("pie", "set", "polar")) {
    if (family_name == "set") plot_set(frame, title_text) else plot_pie_or_set(frame, title_text)
  } else if (family_name %in% c("line", "area", "dual-axis", "radar", "dumbbell")) {
    plot_line_or_area(frame, family_name, title_text)
  } else if (family_name %in% c("scatter", "correlation", "qq", "pca", "roc", "survival")) {
    plot_scatter_family(frame, title_text)
  } else if (family_name %in% c("distribution", "density")) {
    plot_distribution(frame, family_name, title_text)
  } else if (family_name %in% c("heatmap", "matrix")) {
    plot_heatmap(frame, title_text)
  } else if (family_name == "network") {
    plot_network(frame, title_text)
  } else if (family_name == "forest") {
    plot_forest(frame, title_text)
  } else if (family_name %in% c("genome", "epigenome", "sequence")) {
    plot_genome_or_sequence(frame, family_name, title_text)
  } else if (family_name == "pathway") {
    plot_pathway(frame, title_text)
  } else if (family_name == "maf") {
    plot_maf(frame, title_text)
  } else if (family_name == "hierarchy") {
    plot_hierarchy(frame, title_text)
  } else if (family_name == "wordcloud") {
    plot_wordcloud(frame, title_text)
  } else if (family_name %in% c("enrichment", "funnel", "calendar", "stacked-bar", "errorbar", "bar")) {
    plot_bar_like(frame, family_name, title_text)
  } else {
    stop(paste("No plot-specific R renderer registered for family:", family_name))
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
