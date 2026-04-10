-- callout_boxes.lua
-- Convert Pandoc fenced divs (.note, .tip, .warning, .danger, etc.) to
-- coloured callout-box LaTeX environments. Only applies when outputting LaTeX (PDF).
if FORMAT ~= "latex" then return {} end

local callout_colors = {
  note      = "noteblue",
  info      = "noteblue",
  tip       = "tipgreen",
  success   = "tipgreen",
  warning   = "warnyellow",
  caution   = "warnyellow",
  danger    = "dangerred",
  important = "dangerred",
  error     = "dangerred",
}

-- Strip language classes from code blocks so pandoc.write() produces plain
-- verbatim instead of Shaded/Highlighting environments (whose definitions
-- are not available when the code block is rendered inside a Lua filter).
local function strip_code_lang(block)
  if block.t == "CodeBlock" then
    block.classes = {}
    return block
  end
end

-- Saturated text colors for inline bracketed spans [text]{.class}
local span_colors = {
  note      = "textnote",
  info      = "textnote",
  tip       = "texttip",
  success   = "texttip",
  warning   = "textwarn",
  caution   = "textwarn",
  danger    = "textdanger",
  important = "textdanger",
  error     = "textdanger",
}

function Span(el)
  for class, color in pairs(span_colors) do
    if el.classes:includes(class) then
      local content = pandoc.utils.stringify(el.content)
      local latex = string.format("\\textcolor{%s}{\\textbf{%s}}", color, content)
      return pandoc.RawInline("latex", latex)
    end
  end
  return el
end

function Div(el)
  for class, color in pairs(callout_colors) do
    if el.classes:includes(class) then
      local title = el.attributes["title"] or (class:sub(1,1):upper() .. class:sub(2))
      -- Render inner content to LaTeX (strip code highlighting to avoid
      -- undefined Shaded/Highlighting environments)
      local inner_doc = pandoc.Pandoc(el.content):walk({CodeBlock = strip_code_lang})
      local inner_latex = pandoc.write(inner_doc, "latex")
      local latex = string.format(
        "\\begin{calloutbox}{%s}{%s}\n%s\\end{calloutbox}\n",
        color, title, inner_latex
      )
      return pandoc.RawBlock("latex", latex)
    end
  end
  return el
end
