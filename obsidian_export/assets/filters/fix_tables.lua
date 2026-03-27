-- fix_tables.lua
-- Replace Table AST nodes with xltabular RawBlock for PDF output.
-- Uses equal-width X columns (from tabularx) with page-breaking (from longtable).
-- Header rows repeat on continuation pages via \endhead.
if FORMAT ~= "latex" then return {} end

local meta_table_fontsize = nil

function Meta(meta)
  if meta.table_fontsize then
    meta_table_fontsize = pandoc.utils.stringify(meta.table_fontsize)
  end
end

local function cell_to_latex(blocks)
  if #blocks == 0 then return "" end
  local doc = pandoc.Pandoc(blocks)
  local result = pandoc.write(doc, "latex")
  -- Strip document boilerplate, keep body content only
  result = result:match("\\begin{document}%s*(.-)%s*\\end{document}") or result
  -- Assign to local to discard gsub's second return value (substitution count)
  local trimmed = result:gsub("^%s+", ""):gsub("%s+$", "")
  return trimmed
end

local function col_spec(align)
  if align == pandoc.AlignRight then
    return ">{\\raggedleft\\arraybackslash}X"
  elseif align == pandoc.AlignCenter then
    return ">{\\centering\\arraybackslash}X"
  else
    return ">{\\RaggedRight\\arraybackslash}X"
  end
end

function Table(el)
  local n = #el.colspecs
  if n == 0 then return el end

  local col_specs = {}
  for i = 1, n do
    col_specs[i] = col_spec(el.colspecs[i][1])
  end

  local fontsize_cmd = "\\" .. (meta_table_fontsize or "small")
  local lines = {}
  table.insert(lines, "{" .. fontsize_cmd)
  table.insert(lines, "\\begin{xltabular}{\\linewidth}{" .. table.concat(col_specs) .. "}")

  -- Header rows (bold) with longtable continuation headers
  if el.head and el.head.rows and #el.head.rows > 0 then
    -- First page header: toprule + header + midrule
    table.insert(lines, "\\toprule")
    local header_lines = {}
    for _, row in ipairs(el.head.rows) do
      local cells = {}
      for _, cell in ipairs(row.cells) do
        -- pandoc 3.x uses cell.content (not cell.contents)
        local content = cell_to_latex(cell.content or cell.contents or {})
        if content ~= "" then
          table.insert(cells, "\\textbf{" .. content .. "}")
        else
          table.insert(cells, "")
        end
      end
      table.insert(header_lines, table.concat(cells, " & ") .. " \\\\")
    end
    for _, hl in ipairs(header_lines) do
      table.insert(lines, hl)
    end
    table.insert(lines, "\\midrule")
    table.insert(lines, "\\endfirsthead")

    -- Continuation page header: midrule + header + midrule
    table.insert(lines, "\\midrule")
    for _, hl in ipairs(header_lines) do
      table.insert(lines, hl)
    end
    table.insert(lines, "\\midrule")
    table.insert(lines, "\\endhead")
  else
    table.insert(lines, "\\toprule")
  end

  -- Body rows
  for _, body in ipairs(el.bodies) do
    for _, row in ipairs(body.body) do
      local cells = {}
      for _, cell in ipairs(row.cells) do
        local content = cell_to_latex(cell.content or cell.contents or {})
        table.insert(cells, content)
      end
      table.insert(lines, table.concat(cells, " & ") .. " \\\\")
    end
  end

  table.insert(lines, "\\bottomrule")
  table.insert(lines, "\\end{xltabular}")
  table.insert(lines, "}")

  return pandoc.RawBlock("latex", table.concat(lines, "\n"))
end

return {{Meta = Meta}, {Table = Table}}
