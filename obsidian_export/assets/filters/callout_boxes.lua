-- callout_boxes.lua
-- Convert Pandoc fenced divs (.note, .tip, .warning, .danger, etc.) to
-- tcolorbox LaTeX environments. Only applies when outputting LaTeX (PDF).
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

function Div(el)
  for class, color in pairs(callout_colors) do
    if el.classes:includes(class) then
      local title = el.attributes["title"] or (class:sub(1,1):upper() .. class:sub(2))
      -- Render inner content to LaTeX
      local inner_doc = pandoc.Pandoc(el.content)
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
