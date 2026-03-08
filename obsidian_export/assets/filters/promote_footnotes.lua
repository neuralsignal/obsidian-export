-- promote_footnotes.lua
-- Move long external URLs to footnotes at the AST level.
-- Catches any long URLs that stage2 pre-processing didn't handle
-- (e.g., URLs inside existing markdown links).
-- Only promotes URLs longer than URL_THRESHOLD characters.
-- Threshold is read from document metadata (url_footnote_threshold);
-- Python always passes this via --metadata.
local URL_THRESHOLD = 60

function Meta(meta)
  if meta.url_footnote_threshold then
    URL_THRESHOLD = tonumber(pandoc.utils.stringify(meta.url_footnote_threshold)) or 60
  end
end

-- Counter for generating unique footnote anchors
local footnote_count = 0

function Link(el)
  local url = el.target
  -- Only act on external http(s) links with long URLs
  if url:match("^https?://") and #url > URL_THRESHOLD then
    footnote_count = footnote_count + 1
    -- Keep the link text as-is; append a footnote with the full URL
    local note = pandoc.Note({pandoc.Para({pandoc.Str(url)})})
    local inlines = {}
    for _, inline in ipairs(el.content) do
      table.insert(inlines, inline)
    end
    table.insert(inlines, note)
    return inlines
  end
  return el
end

return {{Meta = Meta}, {Link = Link}}
