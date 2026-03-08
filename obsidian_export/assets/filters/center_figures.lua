-- center_figures.lua
-- Promote standalone images (lone image in a paragraph) to centered
-- LaTeX figure environments. Needed because GFM (--from=gfm) treats
-- all images as inline; pandoc never emits \begin{figure}, so
-- \AtBeginEnvironment{figure}{\centering} has no effect.
if FORMAT ~= "latex" then return {} end

function Para(el)
  if #el.content == 1 and el.content[1].t == "Image" then
    local img = el.content[1]
    return pandoc.RawBlock("latex",
      "\\begin{figure}[H]\n" ..
      "\\centering\n" ..
      "\\includegraphics[width=\\maxwidth,height=\\maxheight,keepaspectratio]{" .. img.src .. "}\n" ..
      "\\end{figure}"
    )
  end
end
