-- newpage_on_rule_docx.lua
-- Convert HorizontalRule to an OpenXML page break in DOCX output.
-- In Obsidian notes, --- is commonly used as a section divider
-- where a page break is the intended DOCX behaviour.
if FORMAT ~= "docx" then return {} end

function HorizontalRule()
  return pandoc.RawBlock("openxml", '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
end
