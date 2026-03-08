-- escape_strings.lua
-- Escape LaTeX-special characters (^ and ~) in plain text Str nodes.
-- When ^ or ~ are found, converts the entire Str to a RawInline(latex) with
-- all LaTeX specials properly escaped (including $, &, %, #, _, {, }, \).
-- Only applies when outputting LaTeX (PDF). DOCX and other formats: no-op.
if FORMAT ~= "latex" then return {} end

local function escape_latex_specials(s)
  -- Order matters: escape backslash first to avoid double-escaping
  s = s:gsub("\\", "\\textbackslash{}")
  s = s:gsub("%%", "\\%%")
  s = s:gsub("%$", "\\$")
  s = s:gsub("&", "\\&")
  s = s:gsub("#", "\\#")
  s = s:gsub("_", "\\_")
  s = s:gsub("{", "\\{")
  s = s:gsub("}", "\\}")
  s = s:gsub("%^", "\\^{}")
  s = s:gsub("~", "\\textasciitilde{}")
  return s
end

function Str(el)
  local orig = el.text
  -- Only intercept when ^ or ~ are present; otherwise let pandoc handle normally
  if not (orig:find("%^") or orig:find("~")) then
    return el
  end
  return pandoc.RawInline("latex", escape_latex_specials(orig))
end
