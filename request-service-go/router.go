package main

import (
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strconv"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

type Route struct {
	Keyword     string  `yaml:"keyword"`
	Pattern     string  `yaml:"pattern"`
	URL         string  `yaml:"url"`
	Method      string  `yaml:"method"`      // e.g., "GET", "POST"
	ContentType string  `yaml:"contentType"` // e.g., "application/x-www-form-urlencoded"
	Params      []Param `yaml:"params"`
	Match       string  `yaml:"match,omitempty"` // Optional regex to differentiate routes
}

type Param struct {
	Name           string `yaml:"name"`
	Value          string `yaml:"value,omitempty"`            // Static value
	ValueFromInput bool   `yaml:"value_from_input,omitempty"` // If true, use user input
}

type Config struct {
	Routes []Route `yaml:"routes"`
}

func LoadRoutesFromYAML(path string) ([]Route, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var cfg Config
	err = yaml.Unmarshal(data, &cfg)
	if err != nil {
		return nil, err
	}

	return cfg.Routes, nil
}

func callTokenEndpoint(route Route) ([]byte, error) {
	form := url.Values{}
	for _, p := range route.Params {
		form.Set(p.Name, p.Value)
	}

	req, err := http.NewRequest(route.Method, route.URL, strings.NewReader(form.Encode()))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", route.ContentType)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	return io.ReadAll(resp.Body)
}

func detectPattern(param string) string {
	if _, err := strconv.Atoi(param); err == nil {
		return "number"
	}

	matched, _ := regexp.MatchString(`^\{[a-fA-F0-9\-]{32,64}\}$`, param)
	if matched {
		return "guid"
	}

	return "any"
}

var routeConfig []Route

func HandleQuery(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	parts := strings.Split(query, " ")

	if len(parts) < 1 {
		http.Error(w, "Invalid query format", http.StatusBadRequest)
		return
	}

	keyword := parts[0]
	param := ""
	if len(parts) > 1 {
		param = parts[1]
	}
	pattern := detectPattern(param)

	var matched *Route
	for _, route := range routeConfig {
		if route.Keyword == keyword {
			if route.Pattern == "token" {
				callTokenEndpoint(route)
			} else if (route.Pattern == "" || route.Pattern == "none") && param == "" {
				matched = &route
				break
			} else if route.Pattern == pattern {
				matched = &route
				break
			}
		}
	}

	if matched == nil {
		http.Error(w, fmt.Sprintf("No matching route for keyword '%s' with pattern '%s'", keyword, pattern), http.StatusNotFound)
		return
	}

	url := strings.Replace(matched.URL, "{param}", param, 1)
	fmt.Printf("Calling URL: %s\n", url)

	resp, err := http.Get(url)
	if err != nil {
		http.Error(w, "Failed to call service", http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	w.Header().Set("Content-Type", "application/json")
	w.Write(body)
}
