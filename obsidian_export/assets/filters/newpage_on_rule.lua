-- newpage_on_rule.lua
-- Convert HorizontalRule to \newpage in LaTeX/PDF output.
-- In Obsidian notes, --- is commonly used as a section divider
-- where a page break is the intended PDF behaviour.
if FORMAT ~= "latex" then return {} end

function HorizontalRule()
  return pandoc.RawBlock("latex", "\\newpage")
end
