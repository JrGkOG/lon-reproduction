#!/usr/bin/env python3
"""Export the active, verified FYP dashboard as a portable static website."""
import argparse
import gzip
import json
from pathlib import Path
import re
import shutil

INDEX = re.compile(r'<script type="application/json" id="study-index">(.*?)</script>', re.S)
ACTIVE = ("seven-binary-study", "burma14", "maxcut700")
URLS = {
    "images": '  images="../../images/"+settings.figures_folder+"/";',
    "export": '  $("export-copies").href=`../${slug}/migration-copies.csv`;',
}
LOCAL_DATA_LOADER = """    if(!window.studyData[slug]){
      await new Promise((resolve,reject)=>{
        const script=document.createElement("script");
        script.src=`../${slug}/viewer-data.js`;
        script.onload=resolve;
        script.onerror=reject;
        document.body.append(script);
      });
    }"""
WEB_LOADER = """    if(!window.studyData[slug]){
      const stream=await fetchGzip(caseAssets(slug)+"study.json.gz");
      window.studyData[slug]=await new Response(stream).json();
    }"""
WEB_HELPERS = '''const caseAssets = slug => `assets/cases/${slug}/`;
async function fetchGzip(url){
  if(!("DecompressionStream" in window)){
    throw new Error("Use a current Chrome, Edge, Firefox, or Safari to open this dashboard.");
  }
  const response=await fetch(url);
  if(!response.ok || !response.body)throw new Error(`Download failed (${response.status}).`);
  return response.body.pipeThrough(new DecompressionStream("gzip"));
}
$("export-copies").addEventListener("click",async event=>{
  event.preventDefault();
  const link=event.currentTarget;
  if(!link.hasAttribute("href") || link.getAttribute("aria-busy")==="true")return;
  const url=link.href;
  const filename=link.download;
  link.setAttribute("aria-busy","true");
  $("export-status").textContent="Preparing CSV…";
  try{
    const bytes=await new Response(await fetchGzip(url)).arrayBuffer();
    const objectURL=URL.createObjectURL(new Blob([bytes],{type:"text/csv;charset=utf-8"}));
    const download=document.createElement("a");
    download.href=objectURL;
    download.download=filename;
    document.body.append(download);
    download.click();
    download.remove();
    setTimeout(()=>URL.revokeObjectURL(objectURL),30000);
    $("export-status").textContent="";
  }catch(error){
    $("export-status").textContent="Could not download the CSV. Try again.";
    console.error(error);
  }finally{
    link.removeAttribute("aria-busy");
  }
});
'''


def replace_once(content, before, after):
    if content.count(before) != 1:
        raise ValueError("The local viewer template changed. Review the web export substitution.")
    return content.replace(before, after, 1)


def write_gzip(path, raw):
    path.write_bytes(gzip.compress(raw, compresslevel=7, mtime=0))
    if gzip.decompress(path.read_bytes()) != raw:
        raise ValueError(f"Compression round-trip failed for {path.name}")


def render_homepage(source):
    for before, after in (
        ('<title>Migrant copies</title>', '<title>Island Migration Dashboard</title>\n'
         '<meta name="description" content="Compare migration, search trajectory networks, and local optima networks across three discrete optimisation problems.">'),
        ('<main class="container">', '<noscript>Enable JavaScript to view the migration dashboard.</noscript>\n<main class="container">'),
        ('<a class="btn" id="export-copies" download>Export CSV</a></div>',
         '<div><a class="btn" id="export-copies" download>Export CSV</a><p id="export-status" role="status"></p></div></div>'),
        (URLS["images"], '  images=caseAssets(slug)+"figures/";'),
        (URLS["export"], '  $("export-copies").href=caseAssets(slug)+"migration-copies.csv.gz";\n'
         '  $("export-copies").download=`${slug}-migration-copies.csv`;'),
        ('async function changeProblem(){', WEB_HELPERS+'\nasync function changeProblem(){'),
        (LOCAL_DATA_LOADER, WEB_LOADER),
        ('$("load-error").textContent="Could not load this problem. Choose another problem or try again.";',
         '$("load-error").textContent=("DecompressionStream" in window)\n'
         '        ?"Could not load this problem. Choose another problem or reload the page."\n'
         '        :"Use a current browser to view the migration dashboard.";'),
    ):
        source = replace_once(source, before, after)
    return source


def export_case(project, public, slug, methods):
    directory = project / "output/analysis" / slug
    prefix = f'window.studyData["{slug}"]='
    js = (directory / "viewer-data.js").read_text(encoding="utf-8").strip()
    if not js.startswith(prefix) or not js.endswith(";"):
        raise ValueError(f"Unexpected viewer data format for {slug}")
    serialized = js[len(prefix):-1].encode("utf-8")
    data = json.loads(serialized)
    if data["methods"] != methods or len(data["pairs"]) != 70 or len(data["events"]) != 4200:
        raise ValueError(f"Incomplete study or mismatched methods for {slug}")
    assets = public / "assets/cases" / slug
    figures = assets / "figures"
    figures.mkdir(parents=True)
    write_gzip(assets / "study.json.gz", serialized)
    write_gzip(assets / "migration-copies.csv.gz", (directory / "migration-copies.csv").read_bytes())
    image_names = {data["study"]["reference_image"], *(row["figure"] for row in data["pairs"])}
    if len(image_names) != 71 or any(Path(name).name != name or not name.endswith(".png") for name in image_names):
        raise ValueError(f"Unexpected image manifest for {slug}")
    images = project / "output/images" / data["study"]["figures_folder"]
    for name in sorted(image_names):
        shutil.copyfile(images / name, figures / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Path to the original lon-reproduction folder")
    parser.add_argument("public", type=Path, help="New directory in which to write the static site")
    args = parser.parse_args()
    source = (args.project / "output/analysis/base-problems/index.html").read_text(encoding="utf-8")
    index = json.loads(INDEX.search(source).group(1))
    if tuple(index["problems"]) != ACTIVE or len(index["methods"]) != 7:
        raise ValueError("The current viewer does not match the intended public study")
    homepage = render_homepage(source)
    args.public.mkdir(parents=True, exist_ok=False)
    for slug in ACTIVE:
        export_case(args.project, args.public, slug, index["methods"])
    (args.public / "index.html").write_text(homepage, encoding="utf-8")


if __name__ == "__main__":
    main()
