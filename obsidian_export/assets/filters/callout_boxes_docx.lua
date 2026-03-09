-- callout_boxes_docx.lua
-- Convert Pandoc fenced divs (.note, .tip, .warning, .danger, etc.) to
-- styled blockquote blocks in DOCX output. Only applies when outputting DOCX.
if FORMAT ~= "docx" then return {} end

local callout_classes = {
  "note", "info", "tip", "success", "warning", "caution", "danger", "important", "error"
}

function Div(el)
  for _, class in ipairs(callout_classes) do
    if el.classes:includes(class) then
      local title = el.attributes["title"] or (class:sub(1, 1):upper() .. class:sub(2))
      local title_para = pandoc.Para({pandoc.Strong({pandoc.Str(title)})})
      local content = {title_para}
      for _, block in ipairs(el.content) do
        table.insert(content, block)
      end
      return pandoc.BlockQuote(content)
    end
  end
  return el
end
